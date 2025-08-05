from __future__ import annotations

import sys
from types import ModuleType, SimpleNamespace
from pathlib import Path

sys.modules["pyarrow"] = SimpleNamespace(__version__="0")
sys.modules.pop("pandas", None)
sys.modules.pop("numpy", None)
sys.modules[
    "yosai_intel_dashboard.src.utils.hashing"
] = SimpleNamespace(hash_dataframe=lambda df: "")
analytics_dir = (
    Path(__file__).resolve().parents[2] / "yosai_intel_dashboard/src/services/analytics"
)
analytics_pkg = ModuleType("yosai_intel_dashboard.src.services.analytics")
analytics_pkg.__path__ = [str(analytics_dir)]
sys.modules["yosai_intel_dashboard.src.services.analytics"] = analytics_pkg
import pandas as pd
import pytest

from tests.infrastructure import uploaded_data
from yosai_intel_dashboard.src.services.analytics.upload_analytics import (
    UploadAnalyticsProcessor,
)



@pytest.fixture
def upload_processor(valid_df):
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
    processor_instance = UploadAnalyticsProcessor(
        vs, processor, callbacks, dynamic_config.analytics, event_bus
    )
    processor_instance.load_uploaded_data = lambda: uploaded_data(
        ("empty.csv", pd.DataFrame()),
        ("valid.csv", valid_df),
    )
    return processor_instance



@pytest.fixture
def valid_df():
    return pd.DataFrame({"Person ID": ["u1", "u2"], "Device name": ["d1", "d2"]})


def test_upload_pipeline_filters_empty_and_returns_stats(upload_processor):
    result = upload_processor.analyze_uploaded_data()

    # Final statistics should reflect only the valid data
    assert result["status"] == "success"
    assert result["rows"] == 2
    assert result["columns"] == 2
