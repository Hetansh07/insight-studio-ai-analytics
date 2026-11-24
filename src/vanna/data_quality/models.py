"""Models returned by the data quality services."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ColumnProfile(BaseModel):
    """Observed quality and distribution facts for one column."""

    name: str
    data_type: str
    row_count: int
    missing_count: int
    missing_percentage: float
    unique_count: int
    duplicate_count: int
    min_value: Any = None
    max_value: Any = None
    mean: Optional[float] = None
    median: Optional[float] = None
    standard_deviation: Optional[float] = None
    top_values: Dict[str, int] = Field(default_factory=dict)
    invalid_count: int = 0
    outlier_count: int = 0


class QualityScores(BaseModel):
    """Transparent 0-100 quality dimensions."""

    completeness: float
    uniqueness: float
    validity: float
    consistency: float
    overall: float


class QualitySummary(BaseModel):
    """Dataset-level quality facts used to explain the score."""

    row_count: int
    column_count: int
    duplicate_row_count: int
    missing_cell_count: int
    invalid_cell_count: int
    outlier_cell_count: int


class DataQualityReport(BaseModel):
    """Complete deterministic profile and quality assessment."""

    summary: QualitySummary
    scores: QualityScores
    columns: List[ColumnProfile]
    issues: List[str] = Field(default_factory=list)
