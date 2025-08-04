import sys
import types
from pathlib import Path

import pytest
from yosai_intel_dashboard.src.core.imports.resolver import safe_import

try:
    import flask  # noqa: F401
except Exception:  # pragma: no cover - skip if missing
    pytest.skip("flask not available", allow_module_level=True)

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

from yosai_intel_dashboard.src.services.analytics.publisher import Publisher  # noqa: E402


class DummyBus:
    def __init__(self):
        self.events = []

    def emit(self, event_type, payload, source=None):
        self.events.append((event_type, payload))


def test_publish_event():
    bus = DummyBus()
    publisher = Publisher(bus)
    publisher.publish({"a": 1}, event="evt")
    assert bus.events == [("evt", {"a": 1})]


def test_publish_without_bus():
    publisher = Publisher(None)
    # should not raise
    publisher.publish({"a": 2})
