import pandas as pd

from services.data_processing.file_handler import FileHandler as FileProcessor
from analytics.upload_processor import UploadAnalyticsProcessor
from services.file_processing_service import FileProcessingService
from services.data_validation import DataValidationService
from services.data_processing.processor import Processor
from services.data_processing.unified_file_validator import UnifiedFileValidator


def _create_components():
    fp = FileProcessor()
    vs = DataValidationService()
    dls = Processor(validator=vs)
    ufv = UnifiedFileValidator()
    fps = FileProcessingService()
    ua = UploadAnalyticsProcessor(fps, vs, dls, ufv)
    return fp, ua


def test_process_then_analyze(monkeypatch):
    csv = "Timestamp,Person ID,Token ID,Device name,Access result\n" \
          "2024-01-01 00:00:00,u1,t1,d1,Granted"
    fp, ua = _create_components()
    df, err = fp.process_file(csv.encode(), "sample.csv")
    assert err is None
    assert len(df) == 1

    monkeypatch.setattr(ua, "load_uploaded_data", lambda: {"sample.csv": df})
    result = ua.analyze_uploaded_data()
    assert result["status"] == "success"
    assert result["total_events"] == 1
