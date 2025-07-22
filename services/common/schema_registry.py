"""Simplified Schema Registry client using HTTP requests."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Dict

import requests


@dataclass
class SchemaInfo:
    """Schema metadata returned by the registry."""

    id: int
    version: int
    schema: Dict[str, Any]


class SchemaRegistryClient:
    """Typed client for interacting with a Confluent Schema Registry."""

    def __init__(self, url: str | None = None) -> None:
        self.url = (
            url or os.getenv("SCHEMA_REGISTRY_URL", "http://localhost:8081")
        ).rstrip("/")

    def _get(self, path: str) -> Any:
        resp = requests.get(f"{self.url}{path}", timeout=5)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, payload: Dict[str, Any]) -> Any:
        headers = {"Content-Type": "application/vnd.schemaregistry.v1+json"}
        resp = requests.post(
            f"{self.url}{path}", json=payload, headers=headers, timeout=5
        )
        resp.raise_for_status()
        return resp.json()

    def get_schema(self, subject: str, version: int | str = "latest") -> SchemaInfo:
        data = self._get(f"/subjects/{subject}/versions/{version}")
        return SchemaInfo(
            id=data["id"], version=data["version"], schema=json.loads(data["schema"])
        )

    @lru_cache(maxsize=64)
    def get_schema_by_id(self, schema_id: int) -> SchemaInfo:
        data = self._get(f"/schemas/ids/{schema_id}")
        return SchemaInfo(id=schema_id, version=-1, schema=json.loads(data["schema"]))

    def check_compatibility(
        self, subject: str, schema: Dict[str, Any], version: str = "latest"
    ) -> bool:
        data = self._post(
            f"/compatibility/subjects/{subject}/versions/{version}",
            {"schema": json.dumps(schema)},
        )
        return bool(data.get("is_compatible"))


__all__ = ["SchemaRegistryClient", "SchemaInfo"]
