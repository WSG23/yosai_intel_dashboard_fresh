from __future__ import annotations

import asyncio
import builtins
import importlib.util
import pathlib
import sys
import time
import types

import aiohttp
import pytest
from aiohttp import web

# Stub modules to avoid heavy imports during testing
stub_async_batch = types.ModuleType("async_batch")


async def _dummy_async_batch(*args, **kwargs):
    yield []


stub_async_batch.async_batch = _dummy_async_batch
sys.modules.setdefault(
    "yosai_intel_dashboard.src.core.async_utils.async_batch", stub_async_batch
)

stub_tracing = types.ModuleType("tracing")


def propagate_context(_headers):
    return None


stub_tracing.propagate_context = propagate_context
sys.modules.setdefault("tracing", stub_tracing)
dummy_kafka = types.ModuleType("confluent_kafka")


class _DummyBaseProducer:
    def __init__(self, *args, **kwargs):
        pass

    def produce(self, *args, **kwargs):
        pass

    def poll(self, timeout):
        pass

    def list_topics(self, timeout=5):
        raise RuntimeError("down")

    def flush(self, timeout=None):
        pass


dummy_kafka.Producer = _DummyBaseProducer
sys.modules.setdefault("confluent_kafka", dummy_kafka)


class _DummyProfiler:
    def track_task(self, name):
        from contextlib import asynccontextmanager

        @asynccontextmanager
        async def cm():
            yield

        return cm()


builtins.PerformanceProfiler = _DummyProfiler

base_path = pathlib.Path(__file__).resolve().parents[1]

cb_spec = importlib.util.spec_from_file_location(
    "async_circuit_breaker",
    base_path
    / "yosai_intel_dashboard"
    / "src"
    / "core"
    / "async_utils"
    / "async_circuit_breaker.py",
)
cb_mod = importlib.util.module_from_spec(cb_spec)
cb_spec.loader.exec_module(cb_mod)  # type: ignore
CircuitBreakerOpen = cb_mod.CircuitBreakerOpen

rc_spec = importlib.util.spec_from_file_location(
    "rest_client",
    base_path
    / "yosai_intel_dashboard"
    / "src"
    / "infrastructure"
    / "communication"
    / "rest_client.py",
)
rc_mod = importlib.util.module_from_spec(rc_spec)
rc_spec.loader.exec_module(rc_mod)  # type: ignore
RestClient = rc_mod.RestClient
CircuitBreakerOpen = rc_mod.CircuitBreakerOpen

ap_spec = importlib.util.spec_from_file_location(
    "avro_producer",
    base_path
    / "yosai_intel_dashboard"
    / "src"
    / "services"
    / "kafka"
    / "avro_producer.py",
)
ap_mod = importlib.util.module_from_spec(ap_spec)
ap_spec.loader.exec_module(ap_mod)  # type: ignore
AvroProducer = ap_mod.AvroProducer


@pytest.mark.asyncio
async def test_rest_client_recovers_session():
    state = {"ok": False}

    async def handler(request):
        if state["ok"]:
            return web.json_response({"status": "ok"})
        return web.Response(status=500)

    app = web.Application()
    app.router.add_get("/", handler)
    app.router.add_head("/", handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "localhost", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]
    base_url = f"http://localhost:{port}"

    client = RestClient(
        base_url, failure_threshold=1, check_interval=0.1, retries=1, timeout=0.5
    )
    first_session = id(client._session)

    with pytest.raises(aiohttp.ClientResponseError):
        await client.request("GET", "/")

    with pytest.raises(Exception) as exc:
        await client.request("GET", "/")
    assert exc.value.__class__.__name__ == "CircuitBreakerOpen"

    state["ok"] = True
    await asyncio.sleep(0.3)

    second_session = id(client._session)
    assert first_session != second_session

    resp = await client.request("GET", "/")
    assert resp["status"] == "ok"

    await client.close()
    await runner.cleanup()


class DummyProducer:
    def __init__(self):
        self.healthy = False

    def produce(self, *args, **kwargs):
        if not self.healthy:
            raise RuntimeError("down")

    def poll(self, timeout):
        pass

    def list_topics(self, timeout=5):
        if not self.healthy:
            raise RuntimeError("down")

    def flush(self, timeout=None):
        pass


def test_kafka_producer_recovers(monkeypatch):
    dummy = DummyProducer()

    monkeypatch.setattr(
        "yosai_intel_dashboard.src.services.kafka.avro_producer.Producer",
        lambda config: dummy,
    )
    monkeypatch.setattr(
        "yosai_intel_dashboard.src.services.kafka.avro_producer.SchemaRegistryClient",
        lambda url: object(),
    )
    monkeypatch.setattr(AvroProducer, "_encode", lambda self, subject, value: b"data")

    producer = AvroProducer(failure_threshold=1, check_interval=0.1)

    with pytest.raises(RuntimeError):
        producer.produce("t", {}, "s")

    assert producer.circuit_breaker.state == "open"

    dummy.healthy = True
    time.sleep(0.3)

    assert producer.circuit_breaker.state == "closed"

    producer.produce("t", {}, "s")
    producer.close()
