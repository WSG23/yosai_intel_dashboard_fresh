import importlib.util
import pathlib
import sys
import types
import asyncio

import pytest
from fastapi.testclient import TestClient

SERVICES_PATH = pathlib.Path(__file__).resolve().parents[2] / "services"


def load_module():
    otel_stub = types.ModuleType("opentelemetry.instrumentation.fastapi")
    otel_stub.FastAPIInstrumentor = types.SimpleNamespace(instrument_app=lambda *a, **k: None)
    sys.modules.setdefault("opentelemetry.instrumentation.fastapi", otel_stub)

    prom_stub = types.ModuleType("prometheus_fastapi_instrumentator")
    class DummyInstr:
        def instrument(self, app):
            return self
        def expose(self, app):
            return self
    prom_stub.Instrumentator = lambda: DummyInstr()
    sys.modules.setdefault("prometheus_fastapi_instrumentator", prom_stub)
    spec = importlib.util.spec_from_file_location(
        "services.event_ingestion.app",
        SERVICES_PATH / "event-ingestion" / "app.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[arg-type]
    return module


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
