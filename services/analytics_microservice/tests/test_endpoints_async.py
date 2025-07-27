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
sys.modules["services"] = services_stub


def load_app(jwt_secret: str = "secret") -> tuple:

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

    unicode_stub = types.ModuleType("utils.unicode_handler")

    class UnicodeHandler:
        @staticmethod
        def sanitize(value):
            return value

    unicode_stub.UnicodeHandler = UnicodeHandler
    sys.modules.setdefault("utils.unicode_handler", unicode_stub)

    db_stub = types.ModuleType("services.common.async_db")
    db_stub.create_pool = AsyncMock()
    db_stub.close_pool = AsyncMock()
    db_stub.get_pool = AsyncMock(return_value=object())
    sys.modules["services.common.async_db"] = db_stub

    registry_stub = types.ModuleType("services.common.model_registry")

    class ModelRegistry:
        pass

    registry_stub.ModelRegistry = ModelRegistry
    sys.modules.setdefault("services.common.model_registry", registry_stub)

    hvac_stub = types.ModuleType("hvac")
    sys.modules.setdefault("hvac", hvac_stub)

    secrets_stub = types.ModuleType("services.common.secrets")

    def get_secret(_: str) -> str:
        secret = os.getenv("JWT_SECRET", "")
        if not secret or secret == "change-me":
            raise RuntimeError("missing")
        return secret

    secrets_stub.get_secret = get_secret
    sys.modules.setdefault("services.common.secrets", secrets_stub)

    hc_stub = types.ModuleType("infrastructure.discovery.health_check")

    def register_health_check(app, name, func):
        app.state.health_checks = getattr(app.state, "health_checks", {})
        app.state.health_checks[name] = func

    def setup_health_checks(app):
        pass

    hc_stub.register_health_check = register_health_check
    hc_stub.setup_health_checks = setup_health_checks
    sys.modules.setdefault("infrastructure.discovery.health_check", hc_stub)

    config_stub = types.ModuleType("config")

    class _Cfg:
        def get_connection_string(self):
            return "postgresql://"

        initial_pool_size = 1
        max_pool_size = 1
        connection_timeout = 1

    config_stub.get_database_config = lambda: _Cfg()

    class DatabaseSettings:
        def __init__(self, type: str = "", **kwargs):
            self.type = type
            self.host = ""
            self.port = 0
            self.name = ""
            self.user = ""
            self.password = ""
            self.connection_timeout = 1

    config_stub.DatabaseSettings = DatabaseSettings
    sys.modules["config"] = config_stub

    env_stub = types.ModuleType("config.environment")
    env_stub.get_environment = lambda: "test"
    sys.modules["config.environment"] = env_stub

    validate_stub = types.ModuleType("config.validate")
    validate_stub.validate_required_env = lambda vars: None
    sys.modules["config.validate"] = validate_stub

    yf_config_stub = types.ModuleType("yosai_framework.config")

    class DummyCfg:
        service_name = "analytics-test"
        log_level = "INFO"
        metrics_addr = ""
        tracing_endpoint = ""

    yf_config_stub.ServiceConfig = DummyCfg
    yf_config_stub.load_config = lambda path: DummyCfg()
    sys.modules["yosai_framework.config"] = yf_config_stub
    import yosai_framework.service as yf_service

    yf_service.load_config = yf_config_stub.load_config

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

    os.environ["JWT_SECRET"] = jwt_secret

    spec = importlib.util.spec_from_file_location(
        "services.analytics_microservice.app",
        SERVICES_PATH / "analytics_microservice" / "app.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[arg-type]

    # Mark application as ready without running full startup
    module.app.state.ready = True
    module.app.state.startup_complete = True

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
        assert resp.json() == {"status": "ready"}


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
        assert resp.json() == {
            "detail": {"code": "unauthorized", "message": "unauthorized"}
        }


@pytest.mark.asyncio
async def test_model_registry_endpoints(tmp_path):
    module, _, _ = load_app()
    module.app.state.model_dir = tmp_path
    module.app.state.model_registry = {}
    token = jwt.encode(
        {"sub": "svc", "iss": "gateway", "exp": int(time.time()) + 60},
        "secret",
        algorithm="HS256",
    )
    headers = {"Authorization": f"Bearer {token}"}

    transport = httpx.ASGITransport(app=module.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        files = {"file": ("model.bin", b"data")}
        data = {"name": "demo", "version": "1"}
        resp = await client.post(
            "/api/v1/models/register", headers=headers, data=data, files=files
        )
        assert resp.status_code == 200
        assert resp.json()["version"] == "1"

        resp = await client.get("/api/v1/models/demo", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["versions"] == ["1"]

        resp = await client.post(
            "/api/v1/models/demo/rollback",
            headers=headers,
            data={"version": "1"},
        )
        assert resp.status_code == 200
        assert resp.json()["active_version"] == "1"
