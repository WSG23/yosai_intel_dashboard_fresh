from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path
import pandas as pd
import pytest

from tests.utils.builders import DataFrameBuilder

base = Path(__file__).resolve().parents[1] / "yosai_intel_dashboard/src/services/upload"
pkg_name = "yosai_intel_dashboard.src.services.upload"
if pkg_name not in sys.modules:
    pkg = types.ModuleType("upload")
    pkg.__path__ = [str(base)]
    sys.modules[pkg_name] = pkg

spec_proto = importlib.util.spec_from_file_location(
    f"{pkg_name}.protocols", base / "protocols.py"
)
protocols = importlib.util.module_from_spec(spec_proto)
spec_proto.loader.exec_module(protocols)
sys.modules[f"{pkg_name}.protocols"] = protocols

spec = importlib.util.spec_from_file_location(
    f"{pkg_name}.upload_processing", base / "upload_processing.py"
)
upload_processing = importlib.util.module_from_spec(spec)
spec.loader.exec_module(upload_processing)
UploadAnalyticsProcessor = upload_processing.UploadAnalyticsProcessor


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
    assert result["rows"] == 2
    assert result["columns"] == 2
