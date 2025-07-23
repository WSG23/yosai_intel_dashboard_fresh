import importlib.util
import os
import pathlib
import sys
import types
import time
from unittest.mock import AsyncMock

import httpx
import pytest
from jose import jwt

SERVICES_PATH = pathlib.Path(__file__).resolve().parents[2]

# stub out the heavy 'services' package before pytest imports it
services_stub = types.ModuleType("services")
services_stub.__path__ = [str(SERVICES_PATH)]
sys.modules.setdefault("services", services_stub)


def load_app() -> tuple:

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


    db_stub = types.ModuleType("services.common.async_db")
    db_stub.create_pool = AsyncMock()
    db_stub.close_pool = AsyncMock()
    db_stub.get_pool = AsyncMock(return_value=object())
    sys.modules["services.common.async_db"] = db_stub

    config_stub = types.ModuleType("config")

    class _Cfg:
        def get_connection_string(self):
            return "postgresql://"

        initial_pool_size = 1
        max_pool_size = 1
        connection_timeout = 1

    config_stub.get_database_config = lambda: _Cfg()
    sys.modules["config"] = config_stub

    redis_stub = types.ModuleType("redis")
    redis_async = types.ModuleType("redis.asyncio")
    redis_async.Redis = AsyncMock
    redis_stub.asyncio = redis_async
    sys.modules.setdefault("redis", redis_stub)
    sys.modules.setdefault("redis.asyncio", redis_async)

    queries_stub = types.ModuleType("services.analytics_microservice.async_queries")
    queries_stub.fetch_dashboard_summary = AsyncMock(return_value={"status": "ok"})
    queries_stub.fetch_access_patterns = AsyncMock(return_value={"days": 7})
    sys.modules["services.analytics_microservice.async_queries"] = queries_stub

    os.environ.setdefault("JWT_SECRET", "secret")

    spec = importlib.util.spec_from_file_location(
        "services.analytics_microservice.app",
        SERVICES_PATH / "analytics_microservice" / "app.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[arg-type]

    # base service already registers health routes

    return module, queries_stub, db_stub


@pytest.mark.asyncio
async def test_health_endpoints():
    module, _, _ = load_app()
    transport = httpx.ASGITransport(app=module.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health/live")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

        resp = await client.get("/health/ready")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_dashboard_summary_endpoint():
    module, queries_stub, db_stub = load_app()
    token = jwt.encode(
        {"sub": "svc", "iss": "gateway", "exp": int(time.time()) + 60},
        "secret",
        algorithm="HS256",
    )
    headers = {"Authorization": f"Bearer {token}"}

    transport = httpx.ASGITransport(app=module.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/analytics/get_dashboard_summary", headers=headers
        )
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

    queries_stub.fetch_dashboard_summary.assert_awaited_once()
    db_stub.get_pool.assert_awaited()


@pytest.mark.asyncio
async def test_unauthorized_request():
    module, _, _ = load_app()
    transport = httpx.ASGITransport(app=module.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/v1/analytics/get_dashboard_summary")
        assert resp.status_code == 401
        assert resp.json() == {"code": "unauthorized", "message": "unauthorized"}
