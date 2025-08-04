from __future__ import annotations

import pandas as pd

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


def test_load_data_helper(monkeypatch):
    df = DataFrameBuilder().add_column("A", [1]).build()
    ua = _make_processor()
    monkeypatch.setattr(ua, "load_uploaded_data", lambda: {"f.csv": df})
    assert ua._load_data() == {"f.csv": df}


def test_validate_data_filters_empty():
    df = DataFrameBuilder().add_column("A", [1]).build()
    ua = _make_processor()
    data = {"empty.csv": pd.DataFrame(), "f.csv": df}
    cleaned = ua._validate_data(data)
    assert list(cleaned.keys()) == ["f.csv"]


def test_calculate_statistics():
    df = (
        DataFrameBuilder()
        .add_column("Person ID", ["u1"])
        .add_column("Device name", ["d1"])
        .build()
    )
    ua = _make_processor()
    stats = ua._calculate_statistics({"x.csv": df})
    assert stats["total_events"] == 1
    assert stats["active_users"] == 1
    assert stats["active_doors"] == 1


def test_format_results():
    ua = _make_processor()
    formatted = ua._format_results({"total_events": 1})
    assert formatted["status"] == "success"
    assert formatted["total_events"] == 1
