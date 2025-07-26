from __future__ import annotations

import importlib.util
import sys
from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "schema_registry", Path("services/common/schema_registry.py")
)
schema_registry = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = schema_registry
spec.loader.exec_module(schema_registry)
SchemaRegistryClient = schema_registry.SchemaRegistryClient


class DummyRequest:
    def __init__(self, data: dict):
        self.resp = MagicMock()
        self.resp.json = AsyncMock(return_value=data)
        self.resp.raise_for_status = lambda: None

    async def __aenter__(self):
        return self.resp

    async def __aexit__(self, exc_type, exc, tb):
        pass


class DummySession:
    def __init__(self, data: dict):
        self.data = data

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    def get(self, url: str, timeout=None):
        assert url == "http://sr/subjects/test/versions/latest"
        return DummyRequest(self.data)

    def post(self, url: str, json=None, headers=None, timeout=None):
        return DummyRequest(self.data)


def test_get_schema(monkeypatch, async_runner):
    data = {
        "id": 1,
        "version": 1,
        "schema": '{"type":"record","name":"t","fields":[]}',
    }
    monkeypatch.setattr(aiohttp, "ClientSession", lambda: DummySession(data))
    client = SchemaRegistryClient("http://sr")
    info = async_runner(client.get_schema("test"))
    assert info.id == 1
    assert info.version == 1
    assert info.schema["name"] == "t"


def test_get_schema_cached(monkeypatch, async_runner):
    calls = []

    class CountSession(DummySession):
        def get(self, url: str, timeout=None):
            calls.append(url)
            return super().get(url, timeout)

    data = {
        "id": 1,
        "version": 1,
        "schema": '{"type":"record","name":"t","fields":[]}',
    }
    monkeypatch.setattr(aiohttp, "ClientSession", lambda: CountSession(data))
    client = SchemaRegistryClient("http://sr")
    first = async_runner(client.get_schema("test"))
    second = async_runner(client.get_schema("test"))
    assert first is second
    assert len(calls) == 1


def test_check_compatibility(monkeypatch, async_runner):
    data = {"is_compatible": True}

    class CompatSession(DummySession):
        def post(self, url: str, json=None, headers=None, timeout=None):
            assert url == "http://sr/compatibility/subjects/test/versions/latest"
            return DummyRequest(data)

    monkeypatch.setattr(aiohttp, "ClientSession", lambda: CompatSession(data))
    client = SchemaRegistryClient("http://sr")
    assert async_runner(
        client.check_compatibility("test", {"type": "record", "name": "t", "fields": []})
    )


def test_register_schema(monkeypatch, async_runner):
    data = {"version": 2}

    class RegSession(DummySession):
        def post(self, url: str, json=None, headers=None, timeout=None):
            assert url == "http://sr/subjects/test-value/versions"
            return DummyRequest(data)

    monkeypatch.setattr(aiohttp, "ClientSession", lambda: RegSession(data))
    client = SchemaRegistryClient("http://sr")
    version = async_runner(
        client.register_schema("test-value", {"type": "record", "name": "t", "fields": []})
    )
    assert version == 2
