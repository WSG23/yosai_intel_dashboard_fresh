from __future__ import annotations

import asyncio

import aiohttp
import pytest

import yosai_intel_dashboard.src.infrastructure.communication.rest_client as rest_client
from yosai_intel_dashboard.src.infrastructure.communication.rest_client import (
    AsyncRestClient,
    CircuitBreakerOpen,
)


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


def test_request_propagates_context(monkeypatch):
    called = {}

    def fake_propagate(headers):
        called["headers"] = headers.copy()

    def fake_request(self, method, url, **kwargs):
        called["url"] = url
        return FakeResponse()

    monkeypatch.setattr(rest_client, "propagate_context", fake_propagate)
    monkeypatch.setattr(aiohttp.ClientSession, "request", fake_request)

    client = AsyncRestClient("http://svc.ns.svc.cluster.local")

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

    monkeypatch.setattr(rest_client, "propagate_context", lambda h: None)
    monkeypatch.setattr(aiohttp.ClientSession, "request", fake_request)

    client = AsyncRestClient("http://svc.ns.svc.cluster.local", retries=3)

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

    client = AsyncRestClient("http://svc.ns.svc.cluster.local")
    monkeypatch.setattr(aiohttp.ClientSession, "request", fake_request)

    async def always_false():
        return False

    monkeypatch.setattr(client.circuit_breaker, "allows_request", always_false)

    async def run():
        with pytest.raises(CircuitBreakerOpen):
            await client.request("GET", "/")

    asyncio.run(run())
    assert called is False
