"""Simplified Schema Registry client using HTTP requests."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict

import aiohttp
from asyncio import Lock
from monitoring.data_quality_monitor import get_data_quality_monitor


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
        self._schema_cache: Dict[tuple[str, str], SchemaInfo] = {}
        self._id_cache: Dict[int, SchemaInfo] = {}
        self._lock = Lock()

    async def _get(self, path: str) -> Any:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.url}{path}",
                timeout=aiohttp.ClientTimeout(total=5),
            ) as resp:
                resp.raise_for_status()
                return await resp.json()

    async def _post(self, path: str, payload: Dict[str, Any]) -> Any:
        headers = {"Content-Type": "application/vnd.schemaregistry.v1+json"}
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.url}{path}",
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=5),
            ) as resp:
                resp.raise_for_status()
                return await resp.json()

    async def get_schema(self, subject: str, version: int | str = "latest") -> SchemaInfo:
        key = (subject, str(version))
        async with self._lock:
            if key in self._schema_cache:
                return self._schema_cache[key]
        data = await self._get(f"/subjects/{subject}/versions/{version}")
        info = SchemaInfo(
            id=data["id"], version=data["version"], schema=json.loads(data["schema"])
        )
        async with self._lock:
            self._schema_cache[key] = info
        return info

    async def get_schema_by_id(self, schema_id: int) -> SchemaInfo:
        async with self._lock:
            if schema_id in self._id_cache:
                return self._id_cache[schema_id]
        data = await self._get(f"/schemas/ids/{schema_id}")
        info = SchemaInfo(id=schema_id, version=-1, schema=json.loads(data["schema"]))
        async with self._lock:
            self._id_cache[schema_id] = info
        return info

    async def check_compatibility(
        self, subject: str, schema: Dict[str, Any], version: str = "latest"
    ) -> bool:
        data = await self._post(
            f"/compatibility/subjects/{subject}/versions/{version}",
            {"schema": json.dumps(schema)},
        )
        is_compatible = bool(data.get("is_compatible"))
        if not is_compatible:
            get_data_quality_monitor().record_compatibility_failure()
        return is_compatible

    async def register_schema(self, subject: str, schema: Dict[str, Any]) -> int:
        """Register a new schema version under ``subject`` and return the version."""
        data = await self._post(
            f"/subjects/{subject}/versions",
            {"schema": json.dumps(schema)},
        )
        version = data.get("version")
        if version is None:
            versions = await self._get(f"/subjects/{subject}/versions")
            version = max(versions)

        # invalidate cached schema for this subject
        async with self._lock:
            self._schema_cache.pop((subject, str(version)), None)
            self._id_cache.pop(int(version), None)

        return int(version)

    async def clear_cache(self) -> None:
        async with self._lock:
            self._schema_cache.clear()
            self._id_cache.clear()


__all__ = ["SchemaRegistryClient", "SchemaInfo"]
