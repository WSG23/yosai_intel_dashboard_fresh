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

from yosai_intel_dashboard.src.services.analytics.calculator import Calculator  # noqa: E402


def _make_df():
    return pd.DataFrame(
        {
            "person_id": ["u1", "u2", "u1"],
            "door_id": ["d1", "d2", "d1"],
            "access_result": ["Granted", "Denied", "Granted"],
            "timestamp": [
                "2024-01-01 10:00:00",
                "2024-01-02 11:00:00",
                "2024-01-02 12:00:00",
            ],
        }
    )


def test_analyze_patterns():
    df = _make_df()
    calc = Calculator()
    result = calc.analyze_patterns(df, len(df))
    assert result["data_summary"]["total_records"] == len(df)
    assert result["data_summary"]["unique_entities"]["users"] == 2
