import sys
import types
from pathlib import Path

import pytest
from yosai_intel_dashboard.src.core.imports.resolver import safe_import

try:
    import flask  # noqa: F401
except Exception:  # pragma: no cover - skip if missing
    pytest.skip("flask not available", allow_module_level=True)

import pandas as pd

services_stub = types.ModuleType("services")
services_stub.__path__ = [str(Path(__file__).resolve().parents[1] / "services")]
safe_import('services', services_stub)
safe_import('opentelemetry', types.ModuleType("opentelemetry"))
safe_import('opentelemetry.context', types.ModuleType("otel_ctx"))
safe_import('opentelemetry.propagate', types.ModuleType("otel_prop"))
safe_import('opentelemetry.trace', types.ModuleType("otel_trace"))
sys.modules["opentelemetry.trace"].get_current_span = lambda: types.SimpleNamespace(
    get_span_context=lambda: None
)
sys.modules.setdefault(
    "opentelemetry.exporter.jaeger.thrift", types.ModuleType("otel_jaeger")
)
sys.modules["opentelemetry.exporter.jaeger.thrift"].JaegerExporter = object
safe_import('opentelemetry.sdk.resources', types.ModuleType("otel_res"))
sys.modules["opentelemetry.sdk.resources"].Resource = object
safe_import('opentelemetry.sdk.trace', types.ModuleType("otel_tr_sdk"))
sys.modules["opentelemetry.sdk.trace"].TracerProvider = object
sys.modules.setdefault(
    "opentelemetry.sdk.trace.export", types.ModuleType("otel_tr_exp")
)
sys.modules["opentelemetry.sdk.trace.export"].BatchSpanProcessor = object
safe_import('structlog', types.ModuleType("structlog"))
sys.modules["structlog"].BoundLogger = object

from yosai_intel_dashboard.src.services.analytics.data.loader import DataLoader  # noqa: E402


class DummyUploadProc:
    def __init__(self, data):
        self.data = data

    def load_uploaded_data(self):
        return self.data

    def clean_uploaded_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        return df


class DummyController:
    def __init__(self, data):
        self.data = data
        self.upload_processor = DummyUploadProc(data)

    def load_uploaded_data(self):
        return self.data

    def clean_uploaded_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        return df

    def summarize_dataframe(self, df: pd.DataFrame):
        return {"rows": len(df)}

    def analyze_with_chunking(self, df: pd.DataFrame, analysis_types):
        return {"types": analysis_types}

    def diagnose_data_flow(self, df: pd.DataFrame):
        return {"rows": len(df)}

    def get_real_uploaded_data(self):
        return {"status": "success"}

    def get_analytics_with_fixed_processor(self):
        return {"status": "success"}


class DummyProcessor:
    def __init__(self, df):
        self.df = df

    def get_processed_database(self):
        return self.df, {}


def test_load_patterns_dataframe():
    df = pd.DataFrame({"a": [1, 2, 3]})
    controller = DummyController({"f.csv": df})
    loader = DataLoader(controller, DummyProcessor(pd.DataFrame()))

    combined, rows = loader.load_patterns_dataframe(None)
    assert rows == len(df)
    assert len(combined) == len(df)


def test_delegated_methods():
    df = pd.DataFrame({"a": [1]})
    controller = DummyController({"f.csv": df})
    loader = DataLoader(controller, DummyProcessor(pd.DataFrame()))

    assert loader.load_uploaded_data() == {"f.csv": df}
    assert loader.clean_uploaded_dataframe(df).equals(df)
    assert loader.summarize_dataframe(df) == {"rows": 1}
    assert loader.analyze_with_chunking(df, ["x"]) == {"types": ["x"]}
    assert loader.diagnose_data_flow(df) == {"rows": 1}
    assert loader.get_real_uploaded_data()["status"] == "success"
    assert loader.get_analytics_with_fixed_processor()["status"] == "success"
