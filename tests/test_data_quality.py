"""Deterministic tests for profiling and safe cleaning."""

import pandas as pd
import pytest

from vanna.data_quality import (
    CleaningAction,
    CleaningExecutor,
    DataProfiler,
    RecommendationEngine,
)


@pytest.fixture
def sample_data() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "category": ["A", "A", "B", None],
            "amount": [10.0, 10.0, None, 100.0],
        }
    )


def test_profile_reports_missing_values_and_duplicates(sample_data: pd.DataFrame) -> None:
    report = DataProfiler().profile(sample_data)

    assert report.summary.row_count == 4
    assert report.summary.column_count == 2
    assert report.summary.missing_cell_count == 2
    assert report.summary.duplicate_row_count == 1
    assert report.scores.overall < 100


def test_recommendations_use_numeric_and_categorical_strategies(
    sample_data: pd.DataFrame,
) -> None:
    recommendations = RecommendationEngine().recommend(sample_data)

    actions = {(item.action, item.column) for item in recommendations}
    assert ("median_imputation", "amount") in actions
    assert ("mode_imputation", "category") in actions
    assert any(item.action == "remove_exact_duplicates" for item in recommendations)


def test_preview_does_not_modify_source(sample_data: pd.DataFrame) -> None:
    original = sample_data.copy(deep=True)
    executor = CleaningExecutor()

    preview = executor.preview(
        sample_data,
        [
            CleaningAction(action="remove_exact_duplicates"),
            CleaningAction(action="median_imputation", column="amount"),
        ],
    )

    pd.testing.assert_frame_equal(sample_data, original)
    assert preview.before_rows == 4
    assert preview.after_rows == 3
    assert preview.after_missing_cells == 1


def test_execution_requires_approval_and_records_version(
    sample_data: pd.DataFrame,
) -> None:
    executor = CleaningExecutor()
    actions = [CleaningAction(action="median_imputation", column="amount")]

    with pytest.raises(ValueError, match="explicit approval"):
        executor.execute(sample_data, actions, approved=False)

    cleaned = executor.execute(sample_data, actions, approved=True)
    assert sample_data["amount"].isna().sum() == 1
    assert cleaned["amount"].isna().sum() == 0
    assert len(executor.history()) == 1
    assert executor.version(cleaned.attrs["operation_id"]).equals(cleaned)
