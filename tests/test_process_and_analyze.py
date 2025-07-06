import pandas as pd

from services.analytics.upload_analytics import UploadAnalyticsProcessor
from services.data_loading_service import DataLoadingService
from services.data_processing.file_processor import FileProcessor
from services.data_validation import DataValidationService


def _create_components():
    from flask import Flask

    from core.cache import cache

    cache.init_app(Flask(__name__))

    fp = FileProcessor()
    vs = DataValidationService()
    dls = DataLoadingService(vs)

    ua = UploadAnalyticsProcessor(vs, dls)
    return fp, ua


def test_process_then_analyze(monkeypatch):
    csv = "Timestamp,Person ID,Token ID,Device name,Access result\n" \
          "2024-01-01 00:00:00,u1,t1,d1,Granted"
    fp, ua = _create_components()
    import base64
    contents = "data:text/csv;base64," + base64.b64encode(csv.encode()).decode()
    df, _ = fp.read_uploaded_file(contents, "sample.csv")
    assert len(df) == 1

    monkeypatch.setattr(ua, "load_uploaded_data", lambda: {"sample.csv": df})
    result = ua.analyze_uploaded_data()
    assert result["status"] == "success"
    assert result["total_events"] == 1
