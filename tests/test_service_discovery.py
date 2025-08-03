import asyncio
from unittest.mock import MagicMock

from yosai_intel_dashboard.src.services.registry import ServiceDiscovery


class DummyResponse:
    def __init__(self, data):
        self._data = data
        self.status = 200

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    def raise_for_status(self):
        pass

    async def json(self):
        return self._data


class DummySession:
    def __init__(self, response=None, exc=None):
        self._response = response
        self._exc = exc
        self.closed = False

    def get(self, url, params=None, headers=None, timeout=None):  # type: ignore[override]
        if self._exc:
            raise self._exc
        return self._response

    async def close(self):
        self.closed = True


def test_resolve_async_cache(monkeypatch):
    handler = MagicMock()
    monkeypatch.setattr(
        "yosai_intel_dashboard.src.services.registry.ErrorHandler", lambda: handler
    )
    monkeypatch.setattr(
        "aiohttp.ClientSession",
        lambda: DummySession(DummyResponse([{"Service": {"Address": "a", "Port": 1}}])),
    )
    sd = ServiceDiscovery("http://registry")
    addr = asyncio.run(sd.resolve_async("svc"))
    assert addr == "a:1"
    sd.session = DummySession(exc=RuntimeError("boom"))
    addr2 = asyncio.run(sd.resolve_async("svc"))
    assert addr2 == "a:1"
    assert handler.handle.called


def test_resolve_async_env(monkeypatch):
    handler = MagicMock()
    monkeypatch.setattr(
        "yosai_intel_dashboard.src.services.registry.ErrorHandler", lambda: handler
    )
    monkeypatch.setenv("FOO_SERVICE_URL", "env:1234")
    monkeypatch.setattr(
        "aiohttp.ClientSession", lambda: DummySession(exc=RuntimeError("boom"))
    )
    sd = ServiceDiscovery("http://registry")
    addr = asyncio.run(sd.resolve_async("foo"))
    assert addr == "env:1234"
    assert handler.handle.called
