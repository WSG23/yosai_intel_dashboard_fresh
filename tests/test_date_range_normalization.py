import types
import sys
from pathlib import Path
import pandas as pd

# Stub dependencies required by DataLoader
controller_module = types.ModuleType('upload_controller')
controller_module.UploadProcessingController = object
sys.modules['yosai_intel_dashboard.src.services.controllers.upload_controller'] = controller_module

processor_module = types.ModuleType('processor')
processor_module.Processor = object
sys.modules['yosai_intel_dashboard.src.services.data_processing.processor'] = processor_module

interfaces_module = types.ModuleType('interfaces')
interfaces_module.ConfigProviderProtocol = object
sys.modules['yosai_intel_dashboard.src.core.interfaces'] = interfaces_module

analytics_pkg = types.ModuleType('analytics')
analytics_pkg.__path__ = [
    str(Path(__file__).resolve().parents[1] / 'yosai_intel_dashboard/src/services/analytics')
]
sys.modules['yosai_intel_dashboard.src.services.analytics'] = analytics_pkg

from yosai_intel_dashboard.src.services.analytics.data.loader import DataLoader


class DummyController:
    def __init__(self):
        self.upload_processor = object()

    def summarize_dataframe(self, df: pd.DataFrame):
        return {
            "rows": len(df),
            "date_range": {"start": "2024-01-01", "end": "2024-01-02"},
        }


class DummyProcessor:
    pass


def test_summarize_dataframe_normalizes_dates():
    df = pd.DataFrame({"a": [1]})
    loader = DataLoader(DummyController(), DummyProcessor())
    summary = loader.summarize_dataframe(df)
    assert summary["date_range"]["start"] == "2024-01-01T00:00:00+00:00"
    assert summary["date_range"]["end"] == "2024-01-02T00:00:00+00:00"
