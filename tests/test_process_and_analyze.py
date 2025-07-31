from yosai_intel_dashboard.src.services.analytics.upload_analytics import UploadAnalyticsProcessor
from yosai_intel_dashboard.src.services.data_processing.file_processor import FileProcessor
from yosai_intel_dashboard.src.services.data_processing.processor import Processor
from tests.builders import TestDataBuilder
from validation.security_validator import SecurityValidator


def _create_components():
    from flask import Flask

    from core.cache import cache

    cache.init_app(Flask(__name__))

    fp = FileProcessor()
    vs = SecurityValidator()
    processor = Processor(validator=vs)

    ua = UploadAnalyticsProcessor(vs, processor)
    return fp, ua


def test_process_then_analyze(monkeypatch):
    fp, ua = _create_components()
    df = TestDataBuilder().add_row().build_dataframe()
    monkeypatch.setattr(ua, "load_uploaded_data", lambda: {"sample.csv": df})
    result = ua.analyze_uploaded_data()
    assert result["status"] == "success"
    assert result["total_events"] == 1
