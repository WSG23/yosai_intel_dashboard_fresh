import importlib.util
import os
import pathlib
import sys
import time
import types

import pytest
from fastapi.testclient import TestClient
from jose import jwt
from yosai_intel_dashboard.src.core.imports.resolver import safe_import

# Stub lightweight services package for microservice import
SERVICES_PATH = pathlib.Path(__file__).resolve().parents[2] / "services"
services_stub = types.ModuleType("services")
services_stub.__path__ = [str(SERVICES_PATH)]
safe_import('services', services_stub)

# Ensure JWT_SECRET_KEY is set for microservice import
os.environ.setdefault("JWT_SECRET_KEY", os.urandom(16).hex())

otel_stub = types.ModuleType("opentelemetry.instrumentation.fastapi")
otel_stub.FastAPIInstrumentor = types.SimpleNamespace(
    instrument_app=lambda *a, **k: None
)
safe_import('opentelemetry.instrumentation.fastapi', otel_stub)

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
safe_import('prometheus_fastapi_instrumentator', prom_stub)


class DummyVault:
    def get_secret(self, path, field=None):
        return "test"

    def invalidate(self, key=None):
        pass


secrets_stub = types.ModuleType(
    "yosai_intel_dashboard.src.services.common.secrets"
)
secrets_stub._init_client = lambda: DummyVault()
secrets_stub.VaultClient = object
secrets_stub.get_secret = lambda key: "test"
secrets_stub.invalidate_secret = lambda key=None: None
safe_import(
    'yosai_intel_dashboard.src.services.common.secrets', secrets_stub
)

# Stub async database module used by the microservice
async_db_stub = types.ModuleType(
    "yosai_intel_dashboard.src.services.common.async_db"
)
async_db_stub.create_pool = lambda *a, **k: None


class DummyPool:
    async def fetch(self, *a, **k):
        return []


async def _get_pool() -> DummyPool:
    return DummyPool()


async_db_stub.get_pool = _get_pool
async_db_stub.close_pool = lambda: None
safe_import('yosai_intel_dashboard.src.services.common.async_db', async_db_stub)

tracing_stub = types.ModuleType("tracing")
tracing_stub.init_tracing = lambda name: None
safe_import('tracing', tracing_stub)


class DummyAnalytics:
    def get_dashboard_summary(self) -> dict:
        return {"status": "ok"}

    def get_access_patterns_analysis(self, days: int = 7) -> dict:
        return {"days": days}


analytics_stub = types.ModuleType("services.analytics_service")
analytics_stub.create_analytics_service = lambda: DummyAnalytics()
safe_import('services.analytics_service', analytics_stub)

# Stub async query functions used by the microservice
async_queries_stub = types.ModuleType("services.analytics_microservice.async_queries")


async def _fetch_summary(pool):
    return {"status": "ok"}


async def _fetch_patterns(pool, days):
    return {"days": days}


async_queries_stub.fetch_dashboard_summary = _fetch_summary
async_queries_stub.fetch_access_patterns = _fetch_patterns
safe_import('services.analytics_microservice.async_queries', async_queries_stub)

# Ensure base health check always succeeds during tests
health_stub = types.ModuleType(
    "yosai_intel_dashboard.src.core.app_factory.health"
)
health_stub.check_critical_dependencies = lambda: (True, None)
safe_import(
    "yosai_intel_dashboard.src.core.app_factory.health", health_stub
)

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
    jwt_secret = os.environ["JWT_SECRET_KEY"]
    bad_token = jwt.encode(
        {"sub": "svc", "iss": "gateway", "exp": int(time.time()) - 1},
        jwt_secret,
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
        jwt_secret,
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
    assert resp.json() == {"status": "healthy"}
