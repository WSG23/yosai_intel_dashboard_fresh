from __future__ import annotations

import importlib
import sys
from types import SimpleNamespace

sys.modules["pyarrow"] = SimpleNamespace(__version__="0")
sys.modules.pop("pandas", None)
sys.modules.pop("numpy", None)
import pandas as pd
import pytest

from tests.fixtures import create_test_upload_processor


@pytest.fixture
def upload_processor(uploaded_data):
    """Instantiate ``UploadAnalyticsProcessor`` configured with mocks."""
    return create_test_upload_processor(uploaded_data)


@pytest.fixture
def valid_df():
    return pd.DataFrame({"Person ID": ["u1", "u2"], "Device name": ["d1", "d2"]})


@pytest.fixture
def uploaded_data(valid_df):
    return {"empty.csv": pd.DataFrame(), "valid.csv": valid_df}


def test_upload_pipeline_filters_empty_and_returns_stats(upload_processor):
    result = upload_processor.analyze_uploaded_data()

    # Final statistics should reflect only the valid data
    assert result["status"] == "success"
    assert result["total_events"] == 2
    assert result["active_users"] == 2
    assert result["active_doors"] == 2
