import asyncio
import pathlib
import sys
import types

import pytest
from tests.import_helpers import safe_import, import_optional

services_path = pathlib.Path(__file__).resolve().parents[1] / "services"
stub_pkg = types.ModuleType("services")
stub_pkg.__path__ = [str(services_path)]
safe_import('services', stub_pkg)

from services.common.model_registry import ModelRegistry


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
