from __future__ import annotations

import importlib.util
import sys
from unittest.mock import MagicMock

from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "schema_registry", Path("services/common/schema_registry.py")
)
schema_registry = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = schema_registry
spec.loader.exec_module(schema_registry)
SchemaRegistryClient = schema_registry.SchemaRegistryClient


def test_get_schema(monkeypatch):
    async def fake_get_async(self, path: str):
        assert path == "/subjects/test/versions/latest"
        return {
            "id": 1,
            "version": 1,
            "schema": '{"type":"record","name":"t","fields":[]}',
        }

    monkeypatch.setattr(SchemaRegistryClient, "_get_async", fake_get_async)
    client = SchemaRegistryClient("http://sr")
    info = client.get_schema("test")
    assert info.id == 1
    assert info.version == 1
    assert info.schema["name"] == "t"


def test_get_schema_cached(monkeypatch):
    calls = []

    async def fake_get_async(self, path: str):
        calls.append(path)
        return {
            "id": 1,
            "version": 1,
            "schema": '{"type":"record","name":"t","fields":[]}',
        }

    monkeypatch.setattr(SchemaRegistryClient, "_get_async", fake_get_async)
    client = SchemaRegistryClient("http://sr")
    first = client.get_schema("test")
    second = client.get_schema("test")
    assert first is second
    assert len(calls) == 1


def test_check_compatibility(monkeypatch):
    async def fake_post_async(self, path: str, payload: dict):
        assert path == "/compatibility/subjects/test/versions/latest"
        return {"is_compatible": True}

    monkeypatch.setattr(SchemaRegistryClient, "_post_async", fake_post_async)
    client = SchemaRegistryClient("http://sr")
    assert client.check_compatibility(
        "test", {"type": "record", "name": "t", "fields": []}
    )


def test_register_schema(monkeypatch):
    async def fake_post_async(self, path: str, payload: dict):
        assert path == "/subjects/test-value/versions"
        return {"version": 2}

    monkeypatch.setattr(SchemaRegistryClient, "_post_async", fake_post_async)
    client = SchemaRegistryClient("http://sr")
    version = client.register_schema(
        "test-value", {"type": "record", "name": "t", "fields": []}
    )
    assert version == 2
