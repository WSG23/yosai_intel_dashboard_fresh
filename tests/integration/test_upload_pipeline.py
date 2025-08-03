import importlib.util
import sys
import types
from pathlib import Path

import pandas as pd
import pytest

from tests.utils.builders import DataFrameBuilder


# ---------------------------------------------------------------------------
# Load ``UploadAnalyticsProcessor`` directly with minimal stubs to avoid heavy
# dependency chains during test import.
MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "yosai_intel_dashboard"
    / "src"
    / "services"
    / "upload"
    / "upload_processing.py"
)

# Create lightweight package stubs for the import hierarchy
for name in [
    "yosai_intel_dashboard",
    "yosai_intel_dashboard.src",
    "yosai_intel_dashboard.src.services",
    "yosai_intel_dashboard.src.services.upload",
]:
    module = types.ModuleType(name)
    module.__path__ = []  # mark as package
    sys.modules.setdefault(name, module)

# Stub the protocols module required by ``upload_processing``
protocols_stub = types.ModuleType(
    "yosai_intel_dashboard.src.services.upload.protocols"
)

class UploadAnalyticsProtocol:  # minimal protocol stub
    def analyze_uploaded_data(self): ...
    def load_uploaded_data(self): ...


protocols_stub.UploadAnalyticsProtocol = UploadAnalyticsProtocol
sys.modules[
    "yosai_intel_dashboard.src.services.upload.protocols"
] = protocols_stub

spec = importlib.util.spec_from_file_location("upload_processing", MODULE_PATH)
upload_module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(upload_module)
UploadAnalyticsProcessor = upload_module.UploadAnalyticsProcessor


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


def test_upload_pipeline_filters_empty_and_returns_stats(upload_processor, uploaded_data, monkeypatch):
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
