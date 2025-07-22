import importlib.util
import pathlib
import sys
import types

import pytest
from fastapi.testclient import TestClient

# Setup stub package path so submodules can be loaded without executing
# the heavy services package.
SERVICES_PATH = pathlib.Path(__file__).resolve().parents[2] / "services"
services_stub = types.ModuleType("services")
services_stub.__path__ = [str(SERVICES_PATH)]
sys.modules.setdefault("services", services_stub)

# Minimal interfaces module so the adapter can import the protocol without
# pulling in heavy dependencies.
interfaces_stub = types.ModuleType("services.interfaces")


class AnalyticsServiceProtocol:
    pass


interfaces_stub.AnalyticsServiceProtocol = AnalyticsServiceProtocol
sys.modules["services.interfaces"] = interfaces_stub


# Provide a minimal analytics service for the microservice
class DummyAnalytics:
    def get_dashboard_summary(self) -> dict:
        return {"status": "ok"}

    def get_access_patterns_analysis(self, days: int = 7) -> dict:
        return {"days": days}


analytics_stub = types.ModuleType("services.analytics_service")
analytics_stub.create_analytics_service = lambda: DummyAnalytics()
sys.modules["services.analytics_service"] = analytics_stub

# Load the FastAPI analytics microservice
app_spec = importlib.util.spec_from_file_location(
    "services.analytics_microservice.app",
    SERVICES_PATH / "analytics_microservice" / "app.py",
)
app_module = importlib.util.module_from_spec(app_spec)
app_spec.loader.exec_module(app_module)

# Load migration adapter utilities
adapter_spec = importlib.util.spec_from_file_location(
    "migration_adapter",
    SERVICES_PATH / "migration" / "adapter.py",
)
migration_adapter = importlib.util.module_from_spec(adapter_spec)
adapter_spec.loader.exec_module(migration_adapter)


@pytest.mark.integration
def test_analytics_service_adapter_microservice(monkeypatch):
    """Adapter should return the same data as the microservice."""
    monkeypatch.setenv("USE_GO_ANALYTICS", "true")
    monkeypatch.setenv("USE_ANALYTICS_MICROSERVICE", "true")

    client = TestClient(app_module.app)

    async def _local_call(self, method: str, params: dict):
        resp = client.post(f"/api/v1/analytics/{method}", json=params)
        return resp.json()

    monkeypatch.setattr(
        migration_adapter.AnalyticsServiceAdapter,
        "_call_microservice",
        _local_call,
    )

    container = migration_adapter.MigrationContainer()
    migration_adapter.register_migration_services(container)

    adapter = container.get("analytics_service")
    expected = client.post("/api/v1/analytics/get_dashboard_summary").json()
    assert adapter.get_dashboard_summary() == expected


@pytest.mark.integration
@pytest.mark.asyncio
async def test_event_service_adapter_kafka(monkeypatch):
    monkeypatch.setenv("USE_GO_EVENTS", "true")

    class DummyFuture:
        def get(self, timeout=None):
            return None

    class DummyProducer:
        def __init__(self, *args, **kwargs):
            pass

        def send(self, topic, key=None, value=None):
            return DummyFuture()

    class FailSession:
        async def __aenter__(self):
            raise AssertionError("HTTP should not be called")

        async def __aexit__(self, exc_type, exc, tb):
            pass

    monkeypatch.setattr(
        migration_adapter.aiohttp, "ClientSession", lambda: FailSession()
    )

    monkeypatch.setattr(migration_adapter, "KafkaProducer", DummyProducer)

    container = migration_adapter.MigrationContainer()
    migration_adapter.register_migration_services(container)

    adapter = container.get("event_processor")
    result = await adapter._process_event({"event_id": "1"})
    assert result["method"] == "kafka"
    assert result["status"] == "accepted"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_event_service_adapter_http_fallback(monkeypatch):
    monkeypatch.setenv("USE_GO_EVENTS", "true")

    class DummyFuture:
        def get(self, timeout=None):
            raise RuntimeError("fail")

    class DummyProducer:
        def __init__(self, *args, **kwargs):
            pass

        def send(self, topic, key=None, value=None):
            return DummyFuture()

    class DummyResponse:
        def __init__(self, data):
            self._data = data

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def json(self):
            return self._data

    class DummySession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        def post(self, url, json=None, timeout=None):
            data = {
                "event_id": json.get("event_id"),
                "status": "accepted",
                "method": "http",
            }
            return DummyResponse(data)

    monkeypatch.setattr(migration_adapter, "KafkaProducer", DummyProducer)
    monkeypatch.setattr(
        migration_adapter.aiohttp, "ClientSession", lambda: DummySession()
    )

    container = migration_adapter.MigrationContainer()
    migration_adapter.register_migration_services(container)

    adapter = container.get("event_processor")
    result = await adapter._process_event({"event_id": "2"})
    assert result["method"] == "http"
    assert result["status"] == "accepted"
