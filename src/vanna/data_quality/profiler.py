"""Deterministic profiling and quality scoring for tabular data."""

from typing import Any, List, Optional

import pandas as pd

from .models import (
    ColumnProfile,
    DataQualityReport,
    QualityScores,
    QualitySummary,
)


class DataProfiler:
    """Profile a DataFrame without modifying the input."""

    def profile(self, dataframe: pd.DataFrame) -> DataQualityReport:
        """Return a profile and transparent quality score for ``dataframe``."""
        dataframe = dataframe.copy(deep=True)
        row_count = len(dataframe)
        column_count = len(dataframe.columns)
        missing_cell_count = int(dataframe.isna().sum().sum())
        duplicate_row_count = int(dataframe.duplicated().sum())
        profiles: List[ColumnProfile] = []

        for name in dataframe.columns:
            series = dataframe[name]
            non_null = series.dropna()
            numeric = pd.api.types.is_numeric_dtype(series)
            missing_count = int(series.isna().sum())
            unique_count = int(series.nunique(dropna=True))
            profile = ColumnProfile(
                name=str(name),
                data_type=str(series.dtype),
                row_count=row_count,
                missing_count=missing_count,
                missing_percentage=self._percentage(missing_count, row_count),
                unique_count=unique_count,
                duplicate_count=max(0, int(len(non_null) - unique_count)),
            )

            if numeric and not non_null.empty:
                profile.min_value = self._scalar(non_null.min())
                profile.max_value = self._scalar(non_null.max())
                profile.mean = self._float_or_none(non_null.mean())
                profile.median = self._float_or_none(non_null.median())
                profile.standard_deviation = self._float_or_none(non_null.std())
                profile.outlier_count = self._outlier_count(non_null)
            elif not non_null.empty:
                profile.top_values = {
                    str(key): int(value)
                    for key, value in non_null.astype(str).value_counts().head(5).items()
                }

            profiles.append(profile)

        total_cells = row_count * column_count
        completeness = self._score(
            1 - (missing_cell_count / total_cells if total_cells else 0)
        )
        uniqueness = self._score(
            1 - (duplicate_row_count / row_count if row_count else 0)
        )
        invalid_cell_count = sum(profile.invalid_count for profile in profiles)
        validity = self._score(
            1 - (invalid_cell_count / total_cells if total_cells else 0)
        )
        outlier_cell_count = sum(profile.outlier_count for profile in profiles)
        consistency = self._score(
            1 - (outlier_cell_count / total_cells if total_cells else 0)
        )
        scores = QualityScores(
            completeness=completeness,
            uniqueness=uniqueness,
            validity=validity,
            consistency=consistency,
            overall=round(
                (completeness + uniqueness + validity + consistency) / 4, 2
            ),
        )
        summary = QualitySummary(
            row_count=row_count,
            column_count=column_count,
            duplicate_row_count=duplicate_row_count,
            missing_cell_count=missing_cell_count,
            invalid_cell_count=invalid_cell_count,
            outlier_cell_count=outlier_cell_count,
        )
        issues = self._issues(profiles, summary)
        return DataQualityReport(
            summary=summary, scores=scores, columns=profiles, issues=issues
        )

    @staticmethod
    def _percentage(value: int, total: int) -> float:
        return round(value * 100 / total, 2) if total else 0.0

    @staticmethod
    def _score(value: float) -> float:
        return round(max(0.0, min(100.0, value * 100)), 2)

    @staticmethod
    def _scalar(value: Any) -> Any:
        return value.item() if hasattr(value, "item") else value

    @staticmethod
    def _float_or_none(value: Any) -> Optional[float]:
        return float(value) if pd.notna(value) else None

    @staticmethod
    def _outlier_count(series: pd.Series) -> int:
        if series.empty:
            return 0
        first_quartile = series.quantile(0.25)
        third_quartile = series.quantile(0.75)
        spread = third_quartile - first_quartile
        if spread == 0:
            return 0
        return int(
            ((series < first_quartile - 1.5 * spread)
             | (series > third_quartile + 1.5 * spread)).sum()
        )

    @staticmethod
    def _issues(
        profiles: List[ColumnProfile], summary: QualitySummary
    ) -> List[str]:
        issues = []
        if summary.duplicate_row_count:
            issues.append(f"{summary.duplicate_row_count} duplicate rows detected.")
        if summary.missing_cell_count:
            issues.append(f"{summary.missing_cell_count} missing cells detected.")
        for profile in profiles:
            if profile.outlier_count:
                issues.append(
                    f"{profile.outlier_count} potential outliers detected in "
                    f"{profile.name}."
                )
        return issues
