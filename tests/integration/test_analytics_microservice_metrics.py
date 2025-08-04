import importlib
import os
import pathlib
import sys
import types

import pytest
from fastapi.testclient import TestClient
from yosai_intel_dashboard.src.core.imports.resolver import safe_import

SERVICES_PATH = pathlib.Path(__file__).resolve().parents[2] / "services"
services_stub = types.ModuleType("services")
services_stub.__path__ = [str(SERVICES_PATH)]
safe_import('services', services_stub)

# Ensure JWT_SECRET for microservice
os.environ.setdefault("JWT_SECRET", os.urandom(16).hex())

# Stub metrics and tracing instrumentation
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

otel_stub = types.ModuleType("opentelemetry.instrumentation.fastapi")
otel_stub.FastAPIInstrumentor = types.SimpleNamespace(
    instrument_app=lambda *a, **k: None
)
safe_import('opentelemetry.instrumentation.fastapi', otel_stub)

# Stub async database module
async_db_stub = types.ModuleType("services.common.async_db")
async_db_stub.create_pool = lambda *a, **k: None


class DummyPool:
    async def fetch(self, *a, **k):
        return []


async def _get_pool() -> DummyPool:
    return DummyPool()


async_db_stub.get_pool = _get_pool
async_db_stub.close_pool = lambda: None
safe_import('services.common.async_db', async_db_stub)


class DummyAnalytics:
    def get_dashboard_summary(self) -> dict:
        return {"status": "ok"}

    def get_access_patterns_analysis(self, days: int = 7) -> dict:
        return {"days": days}


analytics_stub = types.ModuleType("services.analytics_service")
analytics_stub.create_analytics_service = lambda: DummyAnalytics()
safe_import('services.analytics_service', analytics_stub)

async_queries_stub = types.ModuleType("services.analytics_microservice.async_queries")


async def _fetch_summary(pool):
    return {"status": "ok"}


async def _fetch_patterns(pool, days):
    return {"days": days}


async_queries_stub.fetch_dashboard_summary = _fetch_summary
async_queries_stub.fetch_access_patterns = _fetch_patterns
safe_import('services.analytics_microservice.async_queries', async_queries_stub)

dummy_tracing = types.ModuleType("tracing")
called = {}


def fake_init(service_name: str) -> None:
    called["name"] = service_name


dummy_tracing.init_tracing = fake_init
safe_import('tracing', dummy_tracing)


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
