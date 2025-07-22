import importlib
import pathlib
import sys
import types

import pytest
from fastapi.testclient import TestClient

SERVICES_PATH = pathlib.Path(__file__).resolve().parents[2] / "services"
services_stub = types.ModuleType("services")
services_stub.__path__ = [str(SERVICES_PATH)]
sys.modules.setdefault("services", services_stub)

class DummyAnalytics:
    def get_dashboard_summary(self) -> dict:
        return {"status": "ok"}

    def get_access_patterns_analysis(self, days: int = 7) -> dict:
        return {"days": days}

analytics_stub = types.ModuleType("services.analytics_service")
analytics_stub.create_analytics_service = lambda: DummyAnalytics()
sys.modules["services.analytics_service"] = analytics_stub

dummy_tracing = types.ModuleType("tracing")
called = {}

def fake_init(service_name: str) -> None:
    called["name"] = service_name

dummy_tracing.init_tracing = fake_init
sys.modules["tracing"] = dummy_tracing

@pytest.mark.integration
def test_metrics_and_tracing():

    app_spec = importlib.util.spec_from_file_location(
        "services.analytics_microservice.app",
        SERVICES_PATH / "analytics_microservice" / "app.py",
    )
    app_module = importlib.util.module_from_spec(app_spec)
    app_spec.loader.exec_module(app_module)

    assert called.get("name") == "analytics-microservice"

    client = TestClient(app_module.app)
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert b"python_info" in resp.content
