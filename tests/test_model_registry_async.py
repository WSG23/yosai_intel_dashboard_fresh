import asyncio
import pathlib
import sys
from unittest.mock import MagicMock

import pytest

from yosai_intel_dashboard.src.services.common.model_registry import ModelRegistry


class DummyResponse:
    status = 200

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def json(self):
        return {"version": "v1"}

    def raise_for_status(self):
        pass


class DummySession:
    closed = False

    def get(self, url, timeout=None):
        return DummyResponse()

    async def close(self):
        self.closed = True


def test_get_active_version_async(monkeypatch):
    registry = ModelRegistry("http://example.com")
    monkeypatch.setattr(registry, "_session", DummySession())
    version = asyncio.run(registry.get_active_version_async("foo"))
    assert version == "v1"


class FailSession(DummySession):
    def get(self, url, timeout=None):  # type: ignore[override]
        raise RuntimeError("boom")


def test_get_active_version_fallback(monkeypatch):
    registry = ModelRegistry("http://example.com")
    monkeypatch.setattr(registry, "_session", DummySession())
    assert asyncio.run(registry.get_active_version_async("foo")) == "v1"
    handler = MagicMock()
    registry._error_handler = handler
    monkeypatch.setattr(registry, "_session", FailSession())
    version = asyncio.run(registry.get_active_version_async("foo"))
    assert version == "v1"
    assert handler.handle.called
