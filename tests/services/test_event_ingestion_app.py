import asyncio
import importlib
import pathlib
import sys
import types
from jose import jwt

import pytest
from fastapi.testclient import TestClient

SERVICES_PATH = pathlib.Path(__file__).resolve().parents[2] / "services"


def load_module():
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
    auth_stub = types.ModuleType("services.auth")
    auth_stub.verify_jwt_token = lambda token: jwt.decode(token, "secret", algorithms=["HS256"])
    sys.modules.setdefault("services.auth", auth_stub)
    sys.path.insert(0, str(SERVICES_PATH / "event-ingestion"))
    sys.modules.get("services").__path__ = [str(SERVICES_PATH)]
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


def test_health_endpoint(monkeypatch):
    module = load_module()
    fake_service = types.SimpleNamespace(
        consume=lambda timeout=1.0: [],
        initialize=lambda: None,
        close=lambda: None,
        health_check=lambda: {"status": "ok"},
    )
    module.service = fake_service
    client = TestClient(module.app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_error_handling_middleware():
    module = load_module()

    @module.app.get("/boom")
    async def _boom():
        raise RuntimeError("fail")

    client = TestClient(module.app)
    resp = client.get("/boom")
    assert resp.status_code == 500
    assert resp.json() == {"code": "internal", "message": "fail"}


def test_verify_jwt_token_util():
    from services.auth import verify_jwt_token
    token = jwt.encode({"iss": "svc"}, "secret", algorithm="HS256")
    claims = verify_jwt_token(token)
    assert claims["iss"] == "svc"
