import asyncio
import socket
from typing import Any, List

import pytest

from infrastructure.discovery.k8s_resolver import K8sResolver


class DummyLoop:
    def __init__(self, addrs: List[str]):
        self.addrs = addrs
        self.called = False

    async def getaddrinfo(self, *args: Any, **kwargs: Any):
        self.called = True
        return [
            (socket.AF_INET, socket.SOCK_STREAM, 6, '', (addr, kwargs.get("port", 0)))
            for addr in self.addrs
        ]


class DummyResp:
    def __init__(self, status: int = 200) -> None:
        self.status = status

    async def __aenter__(self) -> "DummyResp":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        pass


class DummyRequest:
    def __init__(self, status: int = 200) -> None:
        self.resp = DummyResp(status)

    async def __aenter__(self) -> DummyResp:
        return self.resp

    async def __aexit__(self, exc_type, exc, tb) -> None:
        pass


class DummySession:
    def __init__(self, status: int = 200):
        self.status = status

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    def get(self, url, timeout=None):
        return DummyRequest(self.status)


@pytest.mark.asyncio
async def test_resolve_healthy(monkeypatch):
    loop = DummyLoop(["1.1.1.1", "1.1.1.2"])
    monkeypatch.setattr(asyncio, "get_running_loop", lambda: loop)
    monkeypatch.setattr("aiohttp.ClientSession", lambda: DummySession(200))

    resolver = K8sResolver(namespace="ns", cache_ttl=60)
    urls = await resolver.resolve("svc")
    assert urls == ["http://1.1.1.1:80", "http://1.1.1.2:80"]
    assert loop.called

    # cache hit should skip DNS
    loop.called = False
    urls2 = await resolver.resolve("svc")
    assert urls2 == urls
    assert not loop.called


@pytest.mark.asyncio
async def test_resolve_fallback_env(monkeypatch):
    loop = DummyLoop([])
    async def raise_gai(*args, **kwargs):
        raise socket.gaierror
    loop.getaddrinfo = raise_gai
    monkeypatch.setattr(asyncio, "get_running_loop", lambda: loop)
    monkeypatch.setenv("FOO_SERVICE_URL", "http://fallback:1234")

    resolver = K8sResolver(namespace="ns")
    urls = await resolver.resolve("foo", port=1234)
    assert urls == ["http://fallback:1234"]


@pytest.mark.asyncio
async def test_resolve_unhealthy(monkeypatch):
    loop = DummyLoop(["1.1.1.1"])
    monkeypatch.setattr(asyncio, "get_running_loop", lambda: loop)
    monkeypatch.setattr("aiohttp.ClientSession", lambda: DummySession(503))

    resolver = K8sResolver(namespace="ns")
    urls = await resolver.resolve("svc")
    assert urls == []
