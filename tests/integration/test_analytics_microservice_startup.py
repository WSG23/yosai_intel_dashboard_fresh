import importlib.util
import logging
import pathlib
import sys
import types

import pytest
from tests.import_helpers import safe_import, import_optional

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
async_queries_stub = types.ModuleType("services.analytics_microservice.async_queries")
async_queries_stub.fetch_dashboard_summary = lambda *a, **k: {}
async_queries_stub.fetch_access_patterns = lambda *a, **k: {}
safe_import('services.analytics_microservice.async_queries', async_queries_stub)

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
    class DummySecrets:
        def get_secret(self, key):
            raise RuntimeError("missing")

        def invalidate(self, key=None):
            pass

    secrets_mod = types.ModuleType("services.common.secrets")
    secrets_mod.get_secret = DummySecrets().get_secret
    secrets_mod.invalidate_secret = lambda key=None: None
    safe_import('services.common.secrets', secrets_mod)

    app_spec = importlib.util.spec_from_file_location(
        "services.analytics_microservice.app",
        SERVICES_PATH / "analytics_microservice" / "app.py",
    )
    app_module = importlib.util.module_from_spec(app_spec)
    with pytest.raises(RuntimeError):
        app_spec.loader.exec_module(app_module)
