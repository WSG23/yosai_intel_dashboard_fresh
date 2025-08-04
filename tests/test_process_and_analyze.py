from __future__ import annotations

from tests.builders import TestDataBuilder
from validation.security_validator import SecurityValidator
from yosai_intel_dashboard.src.services.analytics.upload_analytics import (
    UploadAnalyticsProcessor,
)
from yosai_intel_dashboard.src.services.data_processing.file_processor import (
    FileProcessor,
)
from yosai_intel_dashboard.src.services.data_processing.processor import Processor


def _create_components():
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

    fp = FileProcessor()
    vs = SecurityValidator()
    processor = Processor(validator=vs)

    event_bus = EventBus()
    callbacks = TrulyUnifiedCallbacks(event_bus=event_bus, security_validator=vs)

    ua = UploadAnalyticsProcessor(
        vs, processor, callbacks, dynamic_config.analytics, event_bus
    )
    return fp, ua


def test_process_then_analyze(monkeypatch):
    fp, ua = _create_components()
    df = TestDataBuilder().add_row().build_dataframe()
    monkeypatch.setattr(ua, "load_uploaded_data", lambda: {"sample.csv": df})
    result = ua.analyze_uploaded_data()
    assert result["status"] == "success"
    assert result["total_events"] == 1
