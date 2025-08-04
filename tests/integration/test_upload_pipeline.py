from __future__ import annotations

import pandas as pd
import pytest

from tests.utils.builders import DataFrameBuilder
from yosai_intel_dashboard.src.services.upload_processing import (
    UploadAnalyticsProcessor,
)


@pytest.fixture
def upload_processor():
    """Instantiate ``UploadAnalyticsProcessor`` for testing."""
    return UploadAnalyticsProcessor()


@pytest.fixture
def valid_df():
    return (
        DataFrameBuilder()
        .add_column("Person ID", ["u1", "u2"])
        .add_column("Device name", ["d1", "d2"])
        .build()
    )


@pytest.fixture
def uploaded_data(valid_df):
    return {"empty.csv": pd.DataFrame(), "valid.csv": valid_df}


def test_upload_pipeline_filters_empty_and_returns_stats(
    upload_processor, uploaded_data, monkeypatch
):
    # Ensure the validation step removes empty dataframes
    validated = upload_processor._validate_data(uploaded_data)
    assert list(validated.keys()) == ["valid.csv"]

    # Simulate uploaded files and run full analysis pipeline
    monkeypatch.setattr(upload_processor, "load_uploaded_data", lambda: uploaded_data)
    result = upload_processor.analyze_uploaded_data()

    # Final statistics should reflect only the valid data
    assert result["status"] == "success"
    assert result["total_events"] == 2
    assert result["active_users"] == 2
    assert result["active_doors"] == 2
