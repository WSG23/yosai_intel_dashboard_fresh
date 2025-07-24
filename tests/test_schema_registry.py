from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from unittest.mock import MagicMock

import requests

spec = importlib.util.spec_from_file_location(
    "schema_registry", Path("services/common/schema_registry.py")
)
schema_registry = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = schema_registry
spec.loader.exec_module(schema_registry)
SchemaRegistryClient = schema_registry.SchemaRegistryClient


def test_get_schema(monkeypatch):
    def fake_get(url: str, timeout: int):
        assert url == "http://sr/subjects/test/versions/latest"
        resp = MagicMock()
        resp.json.return_value = {
            "id": 1,
            "version": 1,
            "schema": '{"type":"record","name":"t","fields":[]}',
        }
        resp.raise_for_status = lambda: None
        return resp

    monkeypatch.setattr(requests, "get", fake_get)
    client = SchemaRegistryClient("http://sr")
    info = client.get_schema("test")
    assert info.id == 1
    assert info.version == 1
    assert info.schema["name"] == "t"


def test_check_compatibility(monkeypatch):
    def fake_post(url: str, json: dict, headers: dict, timeout: int):
        assert url == "http://sr/compatibility/subjects/test/versions/latest"
        resp = MagicMock()
        resp.json.return_value = {"is_compatible": True}
        resp.raise_for_status = lambda: None
        return resp

    monkeypatch.setattr(requests, "post", fake_post)
    client = SchemaRegistryClient("http://sr")
    assert client.check_compatibility(
        "test", {"type": "record", "name": "t", "fields": []}
    )
