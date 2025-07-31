import asyncio
import importlib.util
import pathlib
import sys
import types

import aiohttp
import pytest

services_path = (
    pathlib.Path(__file__).resolve().parents[2]
    / "yosai_intel_dashboard"
    / "src"
    / "services"
)
stub_pkg = types.ModuleType("services")
stub_pkg.__path__ = [str(services_path)]
sys.modules.setdefault("services", stub_pkg)
stub_resilience = types.ModuleType("services.resilience")
stub_resilience.__path__ = [str(services_path / "resilience")]
sys.modules.setdefault("services.resilience", stub_resilience)
stub_tracing = types.ModuleType("tracing")
stub_tracing.propagate_context = lambda headers: None
sys.modules.setdefault("tracing", stub_tracing)

pkg_root = pathlib.Path(__file__).resolve().parents[2] / "yosai_intel_dashboard"
yid_pkg = types.ModuleType("yosai_intel_dashboard")
yid_pkg.__path__ = [str(pkg_root)]
sys.modules.setdefault("yosai_intel_dashboard", yid_pkg)
yid_src_pkg = types.ModuleType("yosai_intel_dashboard.src")
yid_src_pkg.__path__ = [str(pkg_root / "src")]
sys.modules.setdefault("yosai_intel_dashboard.src", yid_src_pkg)

metrics_module = types.ModuleType("services.resilience.metrics")

class DummyCounter:
    def labels(self, *args, **kwargs):
        return self

    def inc(self):
        pass

metrics_module.circuit_breaker_state = DummyCounter()
sys.modules["services.resilience.metrics"] = metrics_module

cb_module = types.ModuleType("services.resilience.circuit_breaker")
from yosai_intel_dashboard.src.core.async_utils.async_circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpen,
    circuit_breaker,
)

cb_module.CircuitBreaker = CircuitBreaker
cb_module.CircuitBreakerOpen = CircuitBreakerOpen
cb_module.circuit_breaker = circuit_breaker
sys.modules["services.resilience.circuit_breaker"] = cb_module

import infrastructure.communication.service_client as service_client

ServiceClient = service_client.ServiceClient
K8sResolver = service_client.K8sResolver
CircuitBreakerOpen = service_client.CircuitBreakerOpen


class FakeResponse:
    status = 200
    headers = {"Content-Type": "application/json"}

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def json(self):
        return {"ok": True}

    async def text(self):
        return '{"ok": true}'

    def raise_for_status(self):
        pass


def test_k8s_resolver():
    resolver = K8sResolver(namespace="ns")
    assert resolver.resolve("svc") == "http://svc.ns.svc.cluster.local"


def test_request_propagates_context(monkeypatch):
    called = {}

    def fake_propagate(headers):
        called["headers"] = headers.copy()

    def fake_request(self, method, url, **kwargs):
        called["url"] = url
        return FakeResponse()

    monkeypatch.setattr(service_client, "propagate_context", fake_propagate)
    monkeypatch.setattr(aiohttp.ClientSession, "request", fake_request)

    client = ServiceClient("svc", resolver=K8sResolver(namespace="ns"))

    async def run():
        return await client.request("GET", "/ping")

    result = asyncio.run(run())
    assert result == {"ok": True}
    assert called["url"].startswith("http://svc.ns.svc.cluster.local")
    assert called["headers"] is not None


def test_retries(monkeypatch):
    attempts = 0

    def fake_request(self, method, url, **kwargs):
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise aiohttp.ClientError("fail")
        return FakeResponse()

    monkeypatch.setattr(service_client, "propagate_context", lambda h: None)
    monkeypatch.setattr(aiohttp.ClientSession, "request", fake_request)

    client = ServiceClient("svc", resolver=K8sResolver(namespace="ns"), retries=3)

    async def run():
        return await client.request("GET", "/")

    result = asyncio.run(run())
    assert result == {"ok": True}
    assert attempts == 3


def test_circuit_breaker_open(monkeypatch):
    called = False

    def fake_request(self, method, url, **kwargs):
        nonlocal called
        called = True
        return FakeResponse()

    client = ServiceClient("svc", resolver=K8sResolver(namespace="ns"))
    monkeypatch.setattr(aiohttp.ClientSession, "request", fake_request)

    async def always_false():
        return False

    monkeypatch.setattr(client.circuit_breaker, "allows_request", always_false)

    async def run():
        with pytest.raises(CircuitBreakerOpen):
            await client.request("GET", "/")

    asyncio.run(run())
    assert called is False
