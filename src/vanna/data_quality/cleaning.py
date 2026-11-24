"""Safe, isolated cleaning previews and versioned execution."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

import pandas as pd
from pydantic import BaseModel, Field


class CleaningAction(BaseModel):
    """One explicitly selected cleaning operation."""

    action: str
    column: Optional[str] = None


class CleaningPreview(BaseModel):
    """Impact calculated from an isolated DataFrame copy."""

    preview_id: str
    before_rows: int
    after_rows: int
    changed_cells: int
    before_missing_cells: int
    after_missing_cells: int
    before_duplicates: int
    after_duplicates: int
    sample_before: List[Dict[str, Any]] = Field(default_factory=list)
    sample_after: List[Dict[str, Any]] = Field(default_factory=list)


class CleaningHistoryEntry(BaseModel):
    """Record of a completed versioned cleaning operation."""

    operation_id: str
    created_at: datetime
    actions: List[CleaningAction]
    before_rows: int
    after_rows: int
    changed_cells: int


class CleaningExecutor:
    """Preview and execute approved actions without mutating the input."""

    def __init__(self) -> None:
        self._history: Dict[str, CleaningHistoryEntry] = {}
        self._versions: Dict[str, pd.DataFrame] = {}

    def preview(self, dataframe: pd.DataFrame, actions: List[CleaningAction]) -> CleaningPreview:
        before = dataframe.copy(deep=True)
        after = self._apply(before, actions)
        return self._preview(before, after)

    def execute(
        self, dataframe: pd.DataFrame, actions: List[CleaningAction], approved: bool
    ) -> pd.DataFrame:
        if not approved:
            raise ValueError("Cleaning execution requires explicit approval")
        before = dataframe.copy(deep=True)
        after = self._apply(before, actions)
        operation_id = str(uuid4())
        self._versions[operation_id] = after.copy(deep=True)
        preview = self._preview(before, after)
        self._history[operation_id] = CleaningHistoryEntry(
            operation_id=operation_id,
            created_at=datetime.now(timezone.utc),
            actions=actions,
            before_rows=preview.before_rows,
            after_rows=preview.after_rows,
            changed_cells=preview.changed_cells,
        )
        result = after.copy(deep=True)
        result.attrs["operation_id"] = operation_id
        return result

    def history(self) -> List[CleaningHistoryEntry]:
        return list(self._history.values())

    def version(self, operation_id: str) -> pd.DataFrame:
        try:
            return self._versions[operation_id].copy(deep=True)
        except KeyError as exc:
            raise KeyError(f"Unknown cleaning operation: {operation_id}") from exc

    def _apply(
        self, dataframe: pd.DataFrame, actions: List[CleaningAction]
    ) -> pd.DataFrame:
        result = dataframe.copy(deep=True)
        for action in actions:
            if action.action == "remove_exact_duplicates":
                result = result.drop_duplicates(ignore_index=True)
            elif action.action in {"median_imputation", "mode_imputation"}:
                if not action.column or action.column not in result.columns:
                    raise ValueError(f"Column is required for {action.action}")
                if action.action == "median_imputation":
                    if not pd.api.types.is_numeric_dtype(result[action.column]):
                        raise ValueError(
                            f"Median imputation requires a numeric column: {action.column}"
                        )
                    value = result[action.column].median()
                else:
                    modes = result[action.column].mode(dropna=True)
                    if modes.empty:
                        raise ValueError(
                            f"Cannot determine a mode for column: {action.column}"
                        )
                    value = modes.iloc[0]
                result[action.column] = result[action.column].fillna(value)
            else:
                raise ValueError(f"Unsupported cleaning action: {action.action}")
        return result

    @staticmethod
    def _preview(before: pd.DataFrame, after: pd.DataFrame) -> CleaningPreview:
        common_columns = [column for column in before.columns if column in after]
        before_aligned = before[common_columns].reset_index(drop=True)
        after_aligned = after[common_columns].reset_index(drop=True)
        comparable_rows = min(len(before_aligned), len(after_aligned))
        changed_cells = int(
            (
                before_aligned.iloc[:comparable_rows].reset_index(drop=True)
                != after_aligned.iloc[:comparable_rows].reset_index(drop=True)
            ).fillna(False).sum().sum()
        )
        return CleaningPreview(
            preview_id=str(uuid4()),
            before_rows=len(before),
            after_rows=len(after),
            changed_cells=changed_cells,
            before_missing_cells=int(before.isna().sum().sum()),
            after_missing_cells=int(after.isna().sum().sum()),
            before_duplicates=int(before.duplicated().sum()),
            after_duplicates=int(after.duplicated().sum()),
            sample_before=before.head(5).to_dict("records"),
            sample_after=after.head(5).to_dict("records"),
        )
