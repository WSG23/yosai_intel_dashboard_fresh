from __future__ import annotations

from tests.utils.builders import DataFrameBuilder
from validation.security_validator import SecurityValidator
from yosai_intel_dashboard.src.services.analytics.upload_analytics import (
    UploadAnalyticsProcessor,
)
from yosai_intel_dashboard.src.services.data_processing.processor import Processor


def _make_processor():
    from flask import Flask

    from yosai_intel_dashboard.src.core.cache import cache
    from yosai_intel_dashboard.src.core.events import EventBus
    from yosai_intel_dashboard.src.infrastructure.callbacks.unified_callbacks import (
        TrulyUnifiedCallbacks,
    )
    from yosai_intel_dashboard.src.infrastructure.config.dynamic_config import (
        dynamic_config,
    )

    cache.init_app(Flask(__name__))

    vs = SecurityValidator()
    processor = Processor(validator=vs)
    event_bus = EventBus()
    callbacks = TrulyUnifiedCallbacks(event_bus=event_bus, security_validator=vs)

    return UploadAnalyticsProcessor(
        vs, processor, callbacks, dynamic_config.analytics, event_bus
    )


def test_direct_processing_helper(tmp_path):
    df1 = (
        DataFrameBuilder()
        .add_column("Timestamp", ["2024-01-01 10:00:00"])
        .add_column("Person ID", ["u1"])
        .add_column("Token ID", ["t1"])
        .add_column("Device name", ["d1"])
        .add_column("Access result", ["Granted"])
        .build()
    )
    proc = _make_processor()
    result = proc._process_uploaded_data_directly({"f1.csv": df1})
    assert result["rows"] == 1
    assert result["columns"] == 5
