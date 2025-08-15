import importlib.util
import logging
import pathlib
import sys
import types

import pytest
from yosai_intel_dashboard.src.core.imports.resolver import safe_import

SERVICES_PATH = pathlib.Path(__file__).resolve().parents[2] / "services"
services_stub = types.ModuleType("services")
services_stub.__path__ = [str(SERVICES_PATH)]
safe_import('services', services_stub)

# Stub instrumentation
prom_stub = types.ModuleType("prometheus_fastapi_instrumentator")


class DummyInstr:
    def instrument(self, app):
        return self

    def expose(self, app):
        return self


prom_stub.Instrumentator = lambda: DummyInstr()
safe_import('prometheus_fastapi_instrumentator', prom_stub)

otel_stub = types.ModuleType("opentelemetry.instrumentation.fastapi")
otel_stub.FastAPIInstrumentor = types.SimpleNamespace(
    instrument_app=lambda *a, **k: None
)
safe_import('opentelemetry.instrumentation.fastapi', otel_stub)

# Stub async database helpers
async_db_stub = types.ModuleType("services.common.async_db")
async_db_stub.create_pool = lambda *a, **k: None
async_db_stub.get_pool = lambda *a, **k: None
async_db_stub.close_pool = lambda: None
safe_import('services.common.async_db', async_db_stub)

# Stub analytics queries
async_queries_stub = types.ModuleType("services.analytics.async_queries")
async_queries_stub.fetch_dashboard_summary = lambda *a, **k: {}
async_queries_stub.fetch_access_patterns = lambda *a, **k: {}
safe_import('services.analytics.async_queries', async_queries_stub)

# Stub tracing
tracing_stub = types.ModuleType("tracing")
tracing_stub.init_tracing = lambda name: None
safe_import('tracing', tracing_stub)

# Stub config
config_stub = types.ModuleType("config")


class DummyCfg:
    def get_connection_string(self):
        return ""

    initial_pool_size = 1
    max_pool_size = 1
    connection_timeout = 1


config_stub.get_database_config = lambda: DummyCfg()
safe_import('config', config_stub)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_startup_requires_jwt_secret(monkeypatch):
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)

    app_spec = importlib.util.spec_from_file_location(
        "services.analytics.app",
        SERVICES_PATH / "analytics" / "app.py",
    )
    app_module = importlib.util.module_from_spec(app_spec)
    app_spec.loader.exec_module(app_module)
    with pytest.raises(RuntimeError):
        await app_module._startup()
