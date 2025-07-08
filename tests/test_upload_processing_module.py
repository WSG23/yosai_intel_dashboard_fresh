import pandas as pd

from services.analytics.upload_analytics import UploadAnalyticsProcessor
from services.data_processing.processor import Processor
from services.data_validation import DataValidationService


def _make_processor():
    from flask import Flask

    from core.cache import cache

    cache.init_app(Flask(__name__))

    vs = DataValidationService()
    processor = Processor(validator=vs)

    return UploadAnalyticsProcessor(vs, processor)

def test_direct_processing_helper(tmp_path):
    df1 = pd.DataFrame(
        {
            "Timestamp": ["2024-01-01 10:00:00"],
            "Person ID": ["u1"],
            "Token ID": ["t1"],
            "Device name": ["d1"],
            "Access result": ["Granted"],
        }
    )
    proc = _make_processor()
    result = proc._process_uploaded_data_directly({"f1.csv": df1})
    assert result["total_events"] == 1
    assert result["active_users"] == 1
    assert result["active_doors"] == 1
