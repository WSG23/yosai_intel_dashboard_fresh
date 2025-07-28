import importlib.util
import os
import pathlib
import sys
import types
import time

import pytest
from fastapi.testclient import TestClient
from jose import jwt

# Stub lightweight services package for microservice import
SERVICES_PATH = pathlib.Path(__file__).resolve().parents[2] / "services"
services_stub = types.ModuleType("services")
services_stub.__path__ = [str(SERVICES_PATH)]
sys.modules.setdefault("services", services_stub)

# Ensure JWT_SECRET is set for microservice import
os.environ.setdefault("JWT_SECRET", "test")

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
        @app.get("/metrics")
        def _metrics():
            return "python_info 1"

        return self


prom_stub.Instrumentator = lambda: DummyInstr()
sys.modules.setdefault("prometheus_fastapi_instrumentator", prom_stub)


class DummyVault:
    def get_secret(self, path, field=None):
        return "test"

    def invalidate(self, key=None):
        pass


common_stub = types.ModuleType("services.common")
common_stub.__path__ = [str(SERVICES_PATH / "common")]
secrets_stub = types.ModuleType("services.common.secrets")
secrets_stub._init_client = lambda: DummyVault()
secrets_stub.VaultClient = object
secrets_stub.get_secret = lambda key: "test"
secrets_stub.invalidate_secret = lambda key=None: None
common_stub.secrets = secrets_stub
sys.modules["services.common"] = common_stub
sys.modules["services.common.secrets"] = secrets_stub

# Stub async database module used by the microservice
async_db_stub = types.ModuleType("services.common.async_db")
async_db_stub.create_pool = lambda *a, **k: None


class DummyPool:
    async def fetch(self, *a, **k):
        return []


async def _get_pool() -> DummyPool:
    return DummyPool()


async_db_stub.get_pool = _get_pool
async_db_stub.close_pool = lambda: None
sys.modules["services.common.async_db"] = async_db_stub

tracing_stub = types.ModuleType("tracing")
tracing_stub.init_tracing = lambda name: None
sys.modules["tracing"] = tracing_stub


class DummyAnalytics:
    def get_dashboard_summary(self) -> dict:
        return {"status": "ok"}

    def get_access_patterns_analysis(self, days: int = 7) -> dict:
        return {"days": days}


analytics_stub = types.ModuleType("services.analytics_service")
analytics_stub.create_analytics_service = lambda: DummyAnalytics()
sys.modules["services.analytics_service"] = analytics_stub

# Stub async query functions used by the microservice
async_queries_stub = types.ModuleType("services.analytics_microservice.async_queries")


async def _fetch_summary(pool):
    return {"status": "ok"}


async def _fetch_patterns(pool, days):
    return {"days": days}


async_queries_stub.fetch_dashboard_summary = _fetch_summary
async_queries_stub.fetch_access_patterns = _fetch_patterns
sys.modules["services.analytics_microservice.async_queries"] = async_queries_stub

app_spec = importlib.util.spec_from_file_location(
    "services.analytics_microservice.app",
    SERVICES_PATH / "analytics_microservice" / "app.py",
)
app_module = importlib.util.module_from_spec(app_spec)
app_spec.loader.exec_module(app_module)


@pytest.mark.integration
def test_requests_without_valid_token_return_401():
    client = TestClient(app_module.app)

    # No Authorization header
    resp = client.get("/v1/analytics/dashboard-summary")
    assert resp.status_code == 401

    # Expired token
    bad_token = jwt.encode(
        {"sub": "svc", "iss": "gateway", "exp": int(time.time()) - 1},
        "test",
        algorithm="HS256",
    )
    resp = client.get(
        "/v1/analytics/dashboard-summary",
        headers={"Authorization": f"Bearer {bad_token}"},
    )
    assert resp.status_code == 401

    # Valid token succeeds
    good_token = jwt.encode(
        {"sub": "svc", "iss": "gateway", "exp": int(time.time()) + 60},
        "test",
        algorithm="HS256",
    )
    resp = client.get(
        "/v1/analytics/dashboard-summary",
        headers={"Authorization": f"Bearer {good_token}"},
    )
    assert resp.status_code == 200


@pytest.mark.integration
def test_health_endpoint():
    client = TestClient(app_module.app)

    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
