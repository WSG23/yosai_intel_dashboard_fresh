import asyncio
import importlib.util
import pathlib
import sys
import types

import aiohttp
import pytest
from tests.import_helpers import safe_import, import_optional

services_path = pathlib.Path(__file__).resolve().parents[2] / "services"
stub_pkg = types.ModuleType("services")
stub_pkg.__path__ = [str(services_path)]
safe_import('services', stub_pkg)
stub_resilience = types.ModuleType("services.resilience")
stub_resilience.__path__ = [str(services_path / "resilience")]
safe_import('services.resilience', stub_resilience)
stub_tracing = types.ModuleType("tracing")
stub_tracing.propagate_context = lambda headers: None
safe_import('tracing', stub_tracing)

metrics_path = services_path / "resilience" / "metrics.py"
metrics_spec = importlib.util.spec_from_file_location(
    "services.resilience.metrics", metrics_path
)
metrics_module = importlib.util.module_from_spec(metrics_spec)
metrics_spec.loader.exec_module(metrics_module)  # type: ignore
safe_import('services.resilience.metrics', metrics_module)

cb_path = services_path / "resilience" / "circuit_breaker.py"
cb_spec = importlib.util.spec_from_file_location(
    "services.resilience.circuit_breaker", cb_path
)
cb_module = importlib.util.module_from_spec(cb_spec)
cb_spec.loader.exec_module(cb_module)  # type: ignore
safe_import('services.resilience.circuit_breaker', cb_module)

module_path = (
    pathlib.Path(__file__).resolve().parents[2] / "adapters" / "service_client.py"
)
spec = importlib.util.spec_from_file_location("service_client", module_path)
service_client = importlib.util.module_from_spec(spec)
spec.loader.exec_module(service_client)  # type: ignore

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
