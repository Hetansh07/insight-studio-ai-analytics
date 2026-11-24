"""Explainable deterministic cleaning recommendations."""

from typing import Any, List, Optional

import pandas as pd
from pydantic import BaseModel

from .models import DataQualityReport


class CleaningRecommendation(BaseModel):
    """A proposed operation backed by observed profile facts."""

    action: str
    column: Optional[str] = None
    affected_records: int
    affected_percentage: float
    reason: str
    risks: str
    expected_impact: str


class RecommendationEngine:
    """Generate recommendations without changing the source DataFrame."""

    def recommend(
        self, dataframe: pd.DataFrame, report: Optional[DataQualityReport] = None
    ) -> List[CleaningRecommendation]:
        recommendations: List[CleaningRecommendation] = []
        row_count = len(dataframe)
        if dataframe.duplicated().any():
            count = int(dataframe.duplicated().sum())
            recommendations.append(
                CleaningRecommendation(
                    action="remove_exact_duplicates",
                    affected_records=count,
                    affected_percentage=self._percentage(count, row_count),
                    reason="Exact duplicate rows reduce uniqueness.",
                    risks="Rows that appear identical may represent legitimate repeated events.",
                    expected_impact=f"Up to {count} duplicate rows would be removed.",
                )
            )

        for column in dataframe.columns:
            missing = int(dataframe[column].isna().sum())
            if not missing:
                continue
            numeric = pd.api.types.is_numeric_dtype(dataframe[column])
            action = "median_imputation" if numeric else "mode_imputation"
            reason = (
                "Median imputation is less sensitive to extreme numeric values."
                if numeric
                else "Mode imputation preserves the most common categorical value."
            )
            recommendations.append(
                CleaningRecommendation(
                    action=action,
                    column=str(column),
                    affected_records=missing,
                    affected_percentage=self._percentage(missing, row_count),
                    reason=reason,
                    risks="Imputation can hide genuine missing-data patterns.",
                    expected_impact=f"{missing} missing values would be filled.",
                )
            )
        return recommendations

    @staticmethod
    def _percentage(value: int, total: int) -> float:
        return round(value * 100 / total, 2) if total else 0.0
