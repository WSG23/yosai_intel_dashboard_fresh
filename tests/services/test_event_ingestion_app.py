from __future__ import annotations

import asyncio
import importlib
import pathlib
import sys
import time
import types

import httpx
import pytest
from fastapi import Depends, FastAPI, HTTPException
from jose import jwt

from yosai_intel_dashboard.src.core.imports.resolver import safe_import

SERVICES_PATH = pathlib.Path(__file__).resolve().parents[2] / "services"


def load_module():
    """Import the event ingestion app with external deps stubbed out."""

    otel_stub = types.ModuleType("opentelemetry.instrumentation.fastapi")
    otel_stub.FastAPIInstrumentor = types.SimpleNamespace(
        instrument_app=lambda *a, **k: None
    )
    safe_import("opentelemetry.instrumentation.fastapi", otel_stub)

    prom_stub = types.ModuleType("prometheus_fastapi_instrumentator")

    class DummyInstr:
        def instrument(self, app):
            return self

        def expose(self, app):
            return self

    prom_stub.Instrumentator = lambda: DummyInstr()
    safe_import("prometheus_fastapi_instrumentator", prom_stub)

    health_stub = types.ModuleType(
        "yosai_intel_dashboard.src.infrastructure.discovery.health_check"
    )
    health_stub.register_health_check = lambda *a, **k: None
    health_stub.setup_health_checks = lambda app: None
    safe_import(
        "yosai_intel_dashboard.src.infrastructure.discovery.health_check",
        health_stub,
    )

    tracing_stub = types.ModuleType("tracing")
    tracing_stub.trace_async_operation = lambda *a, **k: a[-1]
    safe_import("tracing", tracing_stub)

    err_pkg = types.ModuleType("error_handling")
    err_mw = types.ModuleType("error_handling.middleware")
    from fastapi.responses import JSONResponse
    from starlette.middleware.base import BaseHTTPMiddleware

    class DummyMW(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            try:
                return await call_next(request)
            except Exception as exc:  # noqa: BLE001
                return JSONResponse(
                    {
                        "code": "internal",
                        "message": str(exc),
                        "details": None,
                    },
                    status_code=500,
                )

    err_mw.ErrorHandlingMiddleware = DummyMW
    err_pkg.middleware = err_mw
    err_pkg.api_error_response = types.SimpleNamespace()
    safe_import("error_handling", err_pkg)
    safe_import("error_handling.middleware", err_mw)
    sys.modules.setdefault(
        "error_handling.api_error_response", err_pkg.api_error_response
    )

    streaming_stub = types.ModuleType("services.streaming.service")

    class DummyStreamingService:
        def __init__(self, *a, **k):
            pass

        def initialize(self):
            pass

        def consume(self, timeout: float = 1.0):  # pragma: no cover - default
            return []

        def close(self):
            pass

    streaming_stub.StreamingService = DummyStreamingService
    safe_import("services.streaming.service", streaming_stub)
    safe_import("services.streaming", types.ModuleType("services.streaming"))
    sys.modules["services.streaming"].service = streaming_stub

    core_stub = types.ModuleType("core.security")

    class DummyLimiter:
        def __init__(self, *a, **k):
            pass

        async def is_allowed(self, *a, **k):
            return {
                "allowed": True,
                "limit": 100,
                "remaining": 99,
                "reset": time.time() + 60,
            }

        def start_cleanup(self):
            pass

        async def stop_cleanup(self):
            pass

    core_stub.RateLimiter = DummyLimiter
    safe_import("core.security", core_stub)

    safe_import("aiohttp", types.ModuleType("aiohttp"))

    security_stub = types.ModuleType("services.security")
    security_stub.verify_service_jwt = lambda token: {"sub": "svc"}
    safe_import("services.security", security_stub)

    sys.path.insert(0, str(SERVICES_PATH / "event-ingestion"))
    sys.modules.get("services").__path__ = [str(SERVICES_PATH)]

    service_stub = types.ModuleType("yosai_framework.service")

    class DummyService:
        def __init__(self, *a, **k):
            self.app = FastAPI()
            self.app.state.live = True
            self.app.state.ready = True
            self.app.state.startup_complete = True

            @self.app.get("/health")
            async def _health():
                return {"status": "healthy"}

            @self.app.get("/health/live")
            async def _live():
                return {"status": "ok"}

            @self.app.get("/health/ready")
            async def _ready():
                if self.app.state.ready:
                    return {"status": "ready"}
                raise HTTPException(status_code=503, detail="not ready")

            @self.app.get("/health/startup")
            async def _startup():
                if self.app.state.startup_complete:
                    return {"status": "complete"}
                raise HTTPException(status_code=503, detail="starting")

        def start(self):
            pass

        def stop(self, *a):
            pass

    service_stub.BaseService = DummyService
    safe_import("yosai_framework.service", service_stub)

    errors_stub = types.ModuleType("yosai_framework.errors")

    class ServiceError(Exception):
        def __init__(self, code, message):
            self.code = code
            self.message = message

        def to_dict(self):
            return {
                "code": self.code,
                "message": self.message,
                "details": None,
            }

    errors_stub.ServiceError = ServiceError
    safe_import("yosai_framework.errors", errors_stub)

    return importlib.import_module("app")


@pytest.mark.asyncio
async def test_consume_loop_logs(monkeypatch):
    module = load_module()

    messages = [b"a", b"b"]

    def fake_consume(timeout: float = 1.0):
        for m in messages:
            yield m

    fake_service = types.SimpleNamespace(
        consume=fake_consume,
        initialize=lambda: None,
        close=lambda: None,
        health_check=lambda: {"ok": True},
    )
    module.service = fake_service

    seen = []

    class DummyLogger:
        def info(self, msg, value):
            seen.append(value)

    module.app.logger = DummyLogger()

    async def fake_sleep(_):
        raise asyncio.CancelledError()

    monkeypatch.setattr(module, "asyncio", types.SimpleNamespace(sleep=fake_sleep))

    with pytest.raises(asyncio.CancelledError):
        await module._consume_loop()

    assert seen == messages


@pytest.mark.asyncio
async def test_health_endpoint(monkeypatch):
    module = load_module()
    fake_service = types.SimpleNamespace(
        consume=lambda timeout=1.0: [],
        initialize=lambda: None,
        close=lambda: None,
        health_check=lambda: {"status": "ok"},
    )
    module.service = fake_service
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=module.app), base_url="http://test"
    ) as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "healthy"}


@pytest.mark.asyncio
async def test_error_handling_middleware():
    module = load_module()

    @module.app.get("/boom")
    async def _boom():
        raise RuntimeError("fail")

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=module.app), base_url="http://test"
    ) as client:
        resp = await client.get("/boom")
    assert resp.status_code == 500
    assert resp.json() == {"code": "internal", "message": "fail", "details": None}


@pytest.mark.asyncio
async def test_health_ready_endpoint():
    module = load_module()
    module.app.state.ready = True
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=module.app), base_url="http://test"
    ) as client:
        resp = await client.get("/health/ready")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ready"}


@pytest.mark.asyncio
async def test_jwt_validation_failures(monkeypatch):
    module = load_module()

    @module.app.get("/secure", dependencies=[Depends(module.verify_token)])
    async def _secure():
        return {"ok": True}

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=module.app), base_url="http://test"
    ) as client:
        resp = await client.get("/secure")
        assert resp.status_code == 401

        monkeypatch.setattr(module, "verify_service_jwt", lambda *_: None)
        resp = await client.get("/secure", headers={"Authorization": "Bearer bad"})
        assert resp.status_code == 401


@pytest.mark.asyncio
async def test_successful_ingestion_behavior(monkeypatch):
    module = load_module()

    messages = [b"one", b"two"]

    def fake_consume(timeout: float = 1.0):
        for m in messages:
            yield m

    module.service = types.SimpleNamespace(
        consume=fake_consume,
        initialize=lambda: None,
        close=lambda: None,
        health_check=lambda: {"ok": True},
    )

    seen = []

    class DummyLogger:
        def info(self, msg, value):
            seen.append(value)

    module.app.logger = DummyLogger()

    async def fake_sleep(_):
        raise asyncio.CancelledError()

    monkeypatch.setattr(module, "asyncio", types.SimpleNamespace(sleep=fake_sleep))

    with pytest.raises(asyncio.CancelledError):
        await module._consume_loop()

    assert seen == messages
