from yosai_intel_dashboard.src.services.analytics.upload_analytics import UploadAnalyticsProcessor
from yosai_intel_dashboard.src.services.data_processing.processor import Processor
from tests.utils.builders import DataFrameBuilder
from validation.security_validator import SecurityValidator


def _make_processor():
    from flask import Flask

    from core.cache import cache

    cache.init_app(Flask(__name__))

    vs = SecurityValidator()
    processor = Processor(validator=vs)

    return UploadAnalyticsProcessor(vs, processor)


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
    assert result["total_events"] == 1
    assert result["active_users"] == 1
    assert result["active_doors"] == 1
