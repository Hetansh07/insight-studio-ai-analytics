"""SQLite-backed data quality workflow with immutable dataset versions."""

import json
import re
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

import pandas as pd

from .cleaning import CleaningAction, CleaningExecutor
from .models import DataQualityReport
from .profiler import DataProfiler
from .recommendations import CleaningRecommendation, RecommendationEngine

_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_HISTORY_TABLE = "_vanna_data_quality_history"
_DATASETS_TABLE = "_vanna_datasets"
_ALLOWED_UPLOAD_EXTENSIONS = {".csv", ".json", ".xlsx"}
_DEFAULT_MAX_UPLOAD_BYTES = 10 * 1024 * 1024


class SQLiteDataQualityService:
    """Profile and version SQLite tables without replacing source tables."""

    def __init__(self, database_path: str):
        self.database_path = database_path
        self.profiler = DataProfiler()
        self.recommendation_engine = RecommendationEngine()
        self.cleaning_executor = CleaningExecutor()
        self._initialize_metadata()

    def profile(self, dataset_id: str) -> DataQualityReport:
        dataframe = self._read_table(dataset_id)
        return self.profiler.profile(dataframe)

    def list_datasets(
        self, owner_id: Optional[str] = None, is_admin: bool = True
    ) -> List[Dict[str, Any]]:
        """List registered uploads and existing SQLite tables."""
        with sqlite3.connect(self.database_path) as connection:
            registered = connection.execute(
                f"""
                SELECT dataset_id, original_filename, file_type, row_count,
                       column_count, created_at, owner_id
                FROM {_DATASETS_TABLE}
                ORDER BY created_at DESC
                """
            ).fetchall()
            registered_ids = {row[0] for row in registered}
            tables = connection.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type = 'table' AND name NOT LIKE '_vanna_%'
                ORDER BY name
                """
            ).fetchall()

        datasets = [
            {
                "dataset_id": row[0],
                "original_filename": row[1],
                "file_type": row[2],
                "row_count": row[3],
                "column_count": row[4],
                "created_at": row[5],
                "source": "upload",
            }
            for row in registered
            if is_admin or owner_id is None or row[6] == owner_id
        ]
        datasets.extend(
            {
                "dataset_id": row[0],
                "original_filename": None,
                "file_type": "sqlite",
                "row_count": None,
                "column_count": None,
                "created_at": None,
                "source": "database",
            }
            for row in tables
            if row[0] not in registered_ids
        )
        return datasets

    def dataset_preview(self, dataset_id: str, limit: int = 20) -> Dict[str, Any]:
        """Return bounded rows and column metadata for a dataset."""
        if limit < 1 or limit > 1000:
            raise ValueError("Preview limit must be between 1 and 1000")
        dataframe = self._read_table(dataset_id)
        return {
            "dataset_id": dataset_id,
            "columns": [
                {"name": str(column), "data_type": str(dataframe[column].dtype)}
                for column in dataframe.columns
            ],
            "rows": dataframe.head(limit).where(pd.notna(dataframe.head(limit)), None).to_dict(
                "records"
            ),
            "row_count": len(dataframe),
            "column_count": len(dataframe.columns),
        }

    def chart_data(
        self,
        dataset_id: str,
        version_id: Optional[str],
        chart_type: str,
        x_column: str,
        y_column: Optional[str] = None,
        group_by: Optional[str] = None,
        aggregation: str = "sum",
        sort_order: str = "default",
        limit: int = 50,
    ) -> Dict[str, Any]:
        """Build bounded chart data from an authorized dataset version."""
        allowed_types = {
            "bar", "horizontal-bar", "line", "area", "pie", "donut",
            "scatter", "histogram", "box", "heatmap",
        }
        allowed_aggregations = {"sum", "average", "count", "minimum", "maximum", "median"}
        if chart_type not in allowed_types:
            raise ValueError("Unsupported chart type")
        if aggregation not in allowed_aggregations:
            raise ValueError("Unsupported aggregation")
        if sort_order not in {"default", "ascending", "descending"}:
            raise ValueError("Unsupported sort order")
        if limit < 1 or limit > 200:
            raise ValueError("Chart limit must be between 1 and 200")

        table_name = self.resolve_version(dataset_id, version_id)
        dataframe = self._read_table(table_name)
        columns = [
            {"name": str(column), "data_type": str(dataframe[column].dtype),
             "numeric": bool(pd.api.types.is_numeric_dtype(dataframe[column]))}
            for column in dataframe.columns
        ]
        column_names = set(dataframe.columns)
        if x_column not in column_names:
            raise ValueError("Selected X-axis column does not exist")
        for name, label in ((y_column, "Y-axis"), (group_by, "Group By")):
            if name and name not in column_names:
                raise ValueError(f"Selected {label} column does not exist")

        numeric_y = bool(y_column and pd.api.types.is_numeric_dtype(dataframe[y_column]))
        if chart_type in {"scatter", "histogram", "box"} and not numeric_y:
            raise ValueError(f"{chart_type.title()} charts require a numeric Y-axis")
        if chart_type == "heatmap" and (not group_by or not numeric_y):
            raise ValueError("Heatmaps require a categorical Group By and numeric Y-axis")
        if aggregation != "count" and y_column and not numeric_y:
            raise ValueError("Selected Y-axis must be numeric for this aggregation")

        frame = dataframe[[name for name in (x_column, y_column, group_by) if name]].copy()
        if chart_type in {"histogram", "box"}:
            values = frame[y_column].dropna().tolist() if y_column else []
            trace = {"x": values, "type": "histogram" if chart_type == "histogram" else "box",
                     "name": y_column}
        elif chart_type == "heatmap":
            operation = {
                "sum": "sum", "average": "mean", "minimum": "min",
                "maximum": "max", "median": "median", "count": "count",
            }[aggregation]
            pivot = frame.pivot_table(
                index=x_column, columns=group_by, values=y_column,
                aggfunc=operation, dropna=False,
            ).head(limit)
            trace = {
                "x": [str(value) for value in pivot.columns.tolist()],
                "y": [str(value) for value in pivot.index.tolist()],
                "z": pivot.fillna(0).values.tolist(),
                "type": "heatmap",
                "name": y_column,
            }
        elif chart_type == "scatter":
            points = frame.dropna(subset=[x_column, y_column]).head(limit)
            trace = {"x": points[x_column].tolist(), "y": points[y_column].tolist(),
                     "type": "scatter", "mode": "markers", "name": y_column}
        else:
            group_columns = [x_column] + ([group_by] if group_by else [])
            if y_column and aggregation != "count":
                operation = {
                    "sum": "sum", "average": "mean", "minimum": "min",
                    "maximum": "max", "median": "median",
                }[aggregation]
                grouped = frame.groupby(group_columns, dropna=False)[y_column].agg(operation).reset_index(name=y_column)
            else:
                grouped = frame.groupby(group_columns, dropna=False).size().reset_index(name="count")
            value_column = y_column or "count"
            grouped = grouped.dropna(subset=[x_column])
            if sort_order != "default":
                grouped = grouped.sort_values(value_column, ascending=sort_order == "ascending")
            grouped = grouped.head(limit)
            if group_by:
                traces = []
                for group_value, values in grouped.groupby(group_by, dropna=False):
                    trace = {
                        "x": values[x_column].tolist(),
                        "y": values[value_column].tolist(),
                        "type": "bar" if chart_type == "horizontal-bar" else "scatter" if chart_type == "area" else chart_type,
                        "name": str(group_value),
                    }
                    if chart_type == "horizontal-bar":
                        trace["orientation"] = "h"
                    if chart_type == "area":
                        trace["fill"] = "tozeroy"
                    if chart_type in {"pie", "donut"}:
                        trace = {
                            "labels": values[x_column].tolist(),
                            "values": values[value_column].tolist(),
                            "type": "pie",
                            "name": str(group_value),
                            **({"hole": 0.45} if chart_type == "donut" else {}),
                        }
                    traces.append(trace)
                return {"columns": columns, "traces": traces, "summary": {"rows": len(grouped), "value_column": value_column}}
            trace = {
                "x": grouped[x_column].tolist(),
                "y": grouped[value_column].tolist(),
                "type": "bar" if chart_type == "horizontal-bar" else "scatter" if chart_type == "area" else chart_type,
                "name": value_column,
            }
            if chart_type == "horizontal-bar":
                trace["orientation"] = "h"
            if chart_type == "area":
                trace["fill"] = "tozeroy"
            if chart_type in {"pie", "donut"}:
                trace = {
                    "labels": grouped[x_column].tolist(),
                    "values": grouped[value_column].tolist(),
                    "type": "pie",
                    "name": value_column,
                    **({"hole": 0.45} if chart_type == "donut" else {}),
                }
        return {"columns": columns, "traces": [trace], "summary": {"rows": len(trace.get("x", [])), "value_column": y_column or "count"}}

    def upload(
        self,
        filename: str,
        content: bytes,
        *,
        owner_id: Optional[str] = None,
        max_bytes: int = _DEFAULT_MAX_UPLOAD_BYTES,
    ) -> Dict[str, Any]:
        """Persist a validated upload as a new SQLite dataset."""
        safe_filename = Path(filename).name
        extension = Path(safe_filename).suffix.lower()
        if not safe_filename or safe_filename != filename:
            raise ValueError("Invalid upload filename")
        if extension not in _ALLOWED_UPLOAD_EXTENSIONS:
            raise ValueError("Only CSV, JSON, and XLSX files are supported")
        if len(content) == 0:
            raise ValueError("Uploaded file is empty")
        if len(content) > max_bytes:
            raise ValueError(f"Uploaded file exceeds the {max_bytes} byte limit")

        dataframe = self._parse_upload(extension, content)
        if dataframe.shape[1] == 0:
            raise ValueError("Uploaded file must contain at least one column")
        dataset_id = f"dataset_{uuid4().hex[:16]}"
        original_path = (
            Path(self.database_path).resolve().parent
            / "uploads"
            / f"{dataset_id}{extension}"
        )
        original_path.parent.mkdir(parents=True, exist_ok=True)
        original_path.write_bytes(content)
        try:
            with sqlite3.connect(self.database_path) as connection:
                self._write_table(dataframe, dataset_id, connection)
                connection.execute(
                    f"""
                    INSERT INTO {_DATASETS_TABLE}
                    (dataset_id, original_filename, file_type, original_path,
                     row_count, column_count, created_at, owner_id)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        dataset_id,
                        safe_filename,
                        extension[1:],
                        str(original_path),
                        len(dataframe),
                        len(dataframe.columns),
                        datetime.now(timezone.utc).isoformat(),
                        owner_id,
                    ),
                )
        except (OSError, sqlite3.Error, ValueError):
            if original_path.exists():
                original_path.unlink()
            raise
        return self.dataset_metadata(dataset_id)

    def dataset_metadata(self, dataset_id: str) -> Dict[str, Any]:
        self._validate_identifier(dataset_id)
        with sqlite3.connect(self.database_path) as connection:
            row = connection.execute(
                f"""
                SELECT dataset_id, original_filename, file_type, original_path,
                       row_count, column_count, created_at, owner_id
                FROM {_DATASETS_TABLE} WHERE dataset_id = ?
                """,
                (dataset_id,),
            ).fetchone()
        if row:
            return dict(
                zip(
                    (
                        "dataset_id",
                        "original_filename",
                        "file_type",
                        "original_path",
                        "row_count",
                        "column_count",
                        "created_at",
                        "owner_id",
                    ),
                    row,
                )
            )
        self._read_table(dataset_id)
        return {
            "dataset_id": dataset_id,
            "original_filename": None,
            "file_type": "sqlite",
            "original_path": None,
            "row_count": None,
            "column_count": None,
            "created_at": None,
            "owner_id": None,
        }

    def authorize(
        self, dataset_id: str, owner_id: Optional[str], is_admin: bool
    ) -> None:
        """Ensure a caller may access the selected dataset."""
        self._validate_identifier(dataset_id)
        if is_admin:
            self._read_table(dataset_id)
            return
        with sqlite3.connect(self.database_path) as connection:
            row = connection.execute(
                f"SELECT owner_id FROM {_DATASETS_TABLE} WHERE dataset_id = ?",
                (dataset_id,),
            ).fetchone()
        if row is None or not owner_id or row[0] != owner_id:
            raise ValueError("Dataset is not available to this user")
        self._read_table(dataset_id)

    def recommendations(
        self, dataset_id: str
    ) -> List[CleaningRecommendation]:
        dataframe = self._read_table(dataset_id)
        report = self.profiler.profile(dataframe)
        return self.recommendation_engine.recommend(dataframe, report)

    def preview(
        self, dataset_id: str, actions: List[CleaningAction]
    ) -> Dict[str, Any]:
        dataframe = self._read_table(dataset_id)
        before_report = self.profiler.profile(dataframe)
        preview = self.cleaning_executor.preview(dataframe, actions)
        after = self.cleaning_executor._apply(dataframe, actions)
        after_report = self.profiler.profile(after)
        return {
            "dataset_id": dataset_id,
            "preview": preview.model_dump(),
            "quality_before": before_report.model_dump(),
            "quality_after": after_report.model_dump(),
            "warnings": self._warnings(actions),
        }

    def execute(
        self, dataset_id: str, actions: List[CleaningAction], approved: bool
    ) -> Dict[str, Any]:
        if not approved:
            raise ValueError("Cleaning execution requires explicit approval")
        source = self._read_table(dataset_id)
        before_report = self.profiler.profile(source)
        cleaned = self.cleaning_executor.execute(source, actions, approved=True)
        operation_id = str(cleaned.attrs["operation_id"])
        after_report = self.profiler.profile(cleaned)
        preview = self.cleaning_executor._preview(source, cleaned)
        created_at = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.database_path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            previous_version = self._latest_version(dataset_id, connection)
            version_number = self._next_version(dataset_id, connection)
            version_table = f"_vanna_{self._safe_name(dataset_id)}_v{version_number}"
            self._write_table(cleaned, version_table, connection)
            connection.execute(
                f"""
                INSERT INTO {_HISTORY_TABLE}
                (operation_id, dataset_id, original_table, version_table,
                 version_number, previous_version, created_at, actions,
                 affected_rows, affected_cells, quality_before, quality_after,
                 status, error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'completed', NULL)
                """,
                (
                    operation_id,
                    dataset_id,
                    dataset_id,
                    version_table,
                    version_number,
                    previous_version,
                    created_at,
                    json.dumps([action.model_dump() for action in actions]),
                    preview.after_rows - preview.before_rows,
                    preview.changed_cells,
                    json.dumps(before_report.model_dump(), default=str),
                    json.dumps(after_report.model_dump(), default=str),
                ),
            )
        return {
            "operation_id": operation_id,
            "dataset_id": dataset_id,
            "version_id": version_table,
            "version_number": version_number,
            "previous_version": previous_version,
            "preview": preview.model_dump(),
            "quality_before": before_report.model_dump(),
            "quality_after": after_report.model_dump(),
        }

    def history(self, dataset_id: str) -> List[Dict[str, Any]]:
        self._validate_identifier(dataset_id)
        with sqlite3.connect(self.database_path) as connection:
            rows = connection.execute(
                f"""
                SELECT operation_id, dataset_id, original_table, version_table,
                       version_number, previous_version, created_at, actions,
                       affected_rows, affected_cells, quality_before,
                       quality_after, status, error
                FROM {_HISTORY_TABLE}
                WHERE dataset_id = ?
                ORDER BY version_number
                """,
                (dataset_id,),
            ).fetchall()
        return [self._history_row(row) for row in rows]

    def versions(self, dataset_id: str) -> List[Dict[str, Any]]:
        self._validate_identifier(dataset_id)
        versions = [
            {
                "version_id": dataset_id,
                "version_number": 0,
                "is_original": True,
            }
        ]
        for item in self.history(dataset_id):
            versions.append(
                {
                    "version_id": item["version_table"],
                    "version_number": item["version_number"],
                    "is_original": False,
                }
            )
        return versions

    def resolve_version(self, dataset_id: str, version_id: Optional[str]) -> str:
        """Resolve a user selection to a trusted SQLite table identifier."""
        self._validate_identifier(dataset_id)
        if not version_id or version_id == dataset_id:
            self._read_table(dataset_id)
            return dataset_id
        for item in self.history(dataset_id):
            if item["version_table"] == version_id:
                self._read_table(version_id)
                return version_id
        raise ValueError("Selected version does not belong to this dataset")

    def rollback(self, dataset_id: str, version_id: str) -> Dict[str, Any]:
        if version_id == dataset_id:
            source = self._read_table(dataset_id)
        else:
            if not any(item["version_table"] == version_id for item in self.history(dataset_id)):
                raise ValueError("Version does not belong to this dataset")
            source = self._read_table(version_id)
        actions = [CleaningAction(action="rollback", column=version_id)]
        created_at = datetime.now(timezone.utc).isoformat()
        report = self.profiler.profile(source)
        with sqlite3.connect(self.database_path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            version_number = self._next_version(dataset_id, connection)
            version_table = f"_vanna_{self._safe_name(dataset_id)}_v{version_number}"
            previous_version = self._latest_version(dataset_id, connection)
            self._write_table(source, version_table, connection)
            operation_id = (
                f"rollback-{self._safe_name(dataset_id)}-{version_number}"
            )
            connection.execute(
                f"""
                INSERT INTO {_HISTORY_TABLE}
                (operation_id, dataset_id, original_table, version_table,
                 version_number, previous_version, created_at, actions,
                 affected_rows, affected_cells, quality_before, quality_after,
                 status, error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 0, ?, ?, 'completed', NULL)
                """,
                (
                    operation_id,
                    dataset_id,
                    dataset_id,
                    version_table,
                    version_number,
                    previous_version,
                    created_at,
                    json.dumps([action.model_dump() for action in actions]),
                    json.dumps(report.model_dump(), default=str),
                    json.dumps(report.model_dump(), default=str),
                ),
            )
        return {
            "operation_id": operation_id,
            "dataset_id": dataset_id,
            "version_id": version_table,
            "restored_from": version_id,
            "quality": report.model_dump(),
        }

    def _initialize_metadata(self) -> None:
        with sqlite3.connect(self.database_path) as connection:
            connection.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {_DATASETS_TABLE} (
                    dataset_id TEXT PRIMARY KEY,
                    original_filename TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    original_path TEXT NOT NULL,
                    row_count INTEGER NOT NULL,
                    column_count INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    owner_id TEXT
                )
                """
            )
            columns = {
                row[1]
                for row in connection.execute(
                    f"PRAGMA table_info({_DATASETS_TABLE})"
                ).fetchall()
            }
            if "owner_id" not in columns:
                connection.execute(
                    f"ALTER TABLE {_DATASETS_TABLE} ADD COLUMN owner_id TEXT"
                )
            connection.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {_HISTORY_TABLE} (
                    operation_id TEXT PRIMARY KEY,
                    dataset_id TEXT NOT NULL,
                    original_table TEXT NOT NULL,
                    version_table TEXT NOT NULL UNIQUE,
                    version_number INTEGER NOT NULL,
                    previous_version TEXT,
                    created_at TEXT NOT NULL,
                    actions TEXT NOT NULL,
                    affected_rows INTEGER NOT NULL,
                    affected_cells INTEGER NOT NULL,
                    quality_before TEXT NOT NULL,
                    quality_after TEXT NOT NULL,
                    status TEXT NOT NULL,
                    error TEXT
                )
                """
            )

    @staticmethod
    def _parse_upload(extension: str, content: bytes) -> pd.DataFrame:
        try:
            from io import BytesIO

            if extension == ".csv":
                return pd.read_csv(BytesIO(content))
            if extension == ".json":
                return pd.read_json(BytesIO(content))
            return pd.read_excel(BytesIO(content), engine="openpyxl")
        except (ValueError, TypeError, UnicodeDecodeError, ImportError) as exc:
            raise ValueError(
                f"Unable to parse uploaded {extension[1:].upper()} file"
            ) from exc

    def _read_table(self, table_name: str) -> pd.DataFrame:
        self._validate_identifier(table_name)
        with sqlite3.connect(self.database_path) as connection:
            if not self._table_exists(connection, table_name):
                raise ValueError(f"Table does not exist: {table_name}")
            return pd.read_sql_query(
                f'SELECT * FROM "{table_name}"', connection
            )

    def _write_table(
        self,
        dataframe: pd.DataFrame,
        table_name: str,
        connection: Optional[sqlite3.Connection] = None,
    ) -> None:
        self._validate_identifier(table_name)
        if connection is not None:
            dataframe.to_sql(table_name, connection, if_exists="fail", index=False)
            return
        with sqlite3.connect(self.database_path) as owned_connection:
            dataframe.to_sql(
                table_name, owned_connection, if_exists="fail", index=False
            )

    def _next_version(
        self, dataset_id: str, connection: Optional[sqlite3.Connection] = None
    ) -> int:
        if connection is not None:
            row = connection.execute(
                f"SELECT COALESCE(MAX(version_number), 0) FROM {_HISTORY_TABLE} WHERE dataset_id = ?",
                (dataset_id,),
            ).fetchone()
        else:
            with sqlite3.connect(self.database_path) as owned_connection:
                row = owned_connection.execute(
                    f"SELECT COALESCE(MAX(version_number), 0) FROM {_HISTORY_TABLE} WHERE dataset_id = ?",
                    (dataset_id,),
                ).fetchone()
        return int(row[0]) + 1

    def _latest_version(
        self, dataset_id: str, connection: Optional[sqlite3.Connection] = None
    ) -> Optional[str]:
        if connection is not None:
            row = connection.execute(
                f"""
                SELECT version_table FROM {_HISTORY_TABLE}
                WHERE dataset_id = ? ORDER BY version_number DESC LIMIT 1
                """,
                (dataset_id,),
            ).fetchone()
        else:
            with sqlite3.connect(self.database_path) as owned_connection:
                row = owned_connection.execute(
                    f"""
                    SELECT version_table FROM {_HISTORY_TABLE}
                    WHERE dataset_id = ? ORDER BY version_number DESC LIMIT 1
                    """,
                    (dataset_id,),
                ).fetchone()
        return row[0] if row else None

    @staticmethod
    def _validate_identifier(identifier: str) -> None:
        if not _IDENTIFIER.fullmatch(identifier):
            raise ValueError("Invalid dataset identifier")

    @staticmethod
    def _safe_name(identifier: str) -> str:
        return identifier.lower()

    @staticmethod
    def _table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
        return (
            connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
                (table_name,),
            ).fetchone()
            is not None
        )

    @staticmethod
    def _warnings(actions: List[CleaningAction]) -> List[str]:
        if any(action.action == "remove_exact_duplicates" for action in actions):
            return ["Duplicate rows are removed only in the new version."]
        return []

    @staticmethod
    def _history_row(row: tuple) -> Dict[str, Any]:
        keys = (
            "operation_id",
            "dataset_id",
            "original_table",
            "version_table",
            "version_number",
            "previous_version",
            "created_at",
            "actions",
            "affected_rows",
            "affected_cells",
            "quality_before",
            "quality_after",
            "status",
            "error",
        )
        result = dict(zip(keys, row))
        result["actions"] = json.loads(result["actions"])
        result["quality_before"] = json.loads(result["quality_before"])
        result["quality_after"] = json.loads(result["quality_after"])
        return result
