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
def upload_processor():
    """Instantiate ``UploadAnalyticsProcessor`` for testing."""
    from validation.security_validator import SecurityValidator
    from yosai_intel_dashboard.src.core.events import EventBus
    from yosai_intel_dashboard.src.infrastructure.callbacks.unified_callbacks import (
        TrulyUnifiedCallbacks,
    )
    from yosai_intel_dashboard.src.infrastructure.config.dynamic_config import (
        dynamic_config,
    )
    from yosai_intel_dashboard.src.services.data_processing.processor import Processor

    vs = SecurityValidator()
    processor = Processor(validator=vs)
    event_bus = EventBus()
    callbacks = TrulyUnifiedCallbacks(event_bus=event_bus, security_validator=vs)
    return UploadAnalyticsProcessor(
        vs, processor, callbacks, dynamic_config.analytics, event_bus
    )



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
    assert result["rows"] == 2
    assert result["columns"] == 2
