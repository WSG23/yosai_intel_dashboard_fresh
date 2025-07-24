import importlib.util
import pathlib
import sys
import time
import types

import pytest
from fastapi.testclient import TestClient
from jose import jwt

SERVICES_PATH = pathlib.Path(__file__).resolve().parents[2] / "services"


def load_app():
    services_stub = types.ModuleType("services")
    services_stub.__path__ = [str(SERVICES_PATH)]
    sys.modules.setdefault("services", services_stub)

    otel_stub = types.ModuleType("opentelemetry.instrumentation.fastapi")
    otel_stub.FastAPIInstrumentor = types.SimpleNamespace(
        instrument_app=lambda *a, **k: None
    )
    sys.modules.setdefault("opentelemetry.instrumentation.fastapi", otel_stub)

    prom_stub = types.ModuleType("prometheus_fastapi_instrumentator")

    class DummyInstr:
        def instrument(self, app):
            return self

        def expose(self, app):
            return self

    prom_stub.Instrumentator = lambda: DummyInstr()
    sys.modules.setdefault("prometheus_fastapi_instrumentator", prom_stub)

    class DummyAnalytics:
        def __init__(self):
            self.summary_called = 0
            self.pattern_calls = []

        def get_dashboard_summary(self) -> dict:
            self.summary_called += 1
            return {"status": "ok"}

        def get_access_patterns_analysis(self, days: int = 7) -> dict:
            self.pattern_calls.append(days)
            return {"days": days}

    analytics_stub = types.ModuleType("services.analytics_service")
    dummy = DummyAnalytics()
    analytics_stub.create_analytics_service = lambda: dummy
    sys.modules["services.analytics_service"] = analytics_stub

    tracing_stub = types.ModuleType("tracing")
    tracing_stub.init_tracing = lambda name: None
    sys.modules["tracing"] = tracing_stub

    spec = importlib.util.spec_from_file_location(
        "services.analytics_microservice.app",
        SERVICES_PATH / "analytics_microservice" / "app.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[arg-type]
    return module, dummy


@pytest.fixture()
def app_fixture(monkeypatch):
    class DummyVault:
        def get_secret(self, path, field=None):
            return "secret"

        def invalidate(self, key=None):
            pass

    common_stub = types.ModuleType("services.common")
    secrets_stub = types.ModuleType("services.common.secrets")
    secrets_stub._init_client = lambda: DummyVault()
    secrets_stub.get_secret = lambda key: "secret"
    secrets_stub.invalidate_secret = lambda key=None: None
    common_stub.secrets = secrets_stub
    monkeypatch.setitem(sys.modules, "services.common", common_stub)
    monkeypatch.setitem(sys.modules, "services.common.secrets", secrets_stub)
    module, dummy = load_app()
    client = TestClient(module.app)
    return client, dummy


def _token(secret: str) -> str:
    return jwt.encode(
        {"sub": "svc", "iss": "gateway", "exp": int(time.time()) + 60},
        secret,
        algorithm="HS256",
    )


def test_dashboard_summary_endpoint(app_fixture):
    client, dummy = app_fixture
    token = _token("secret")
    resp = client.post(
        "/api/v1/analytics/get_dashboard_summary",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
    assert dummy.summary_called == 1


def test_access_patterns_endpoint(app_fixture):
    client, dummy = app_fixture
    token = _token("secret")
    resp = client.post(
        "/api/v1/analytics/get_access_patterns_analysis",
        json={"days": 3},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json() == {"days": 3}
    assert dummy.pattern_calls == [3]
