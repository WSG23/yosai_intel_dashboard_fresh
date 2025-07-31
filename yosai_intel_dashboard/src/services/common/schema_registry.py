"""Simplified Schema Registry client using HTTP requests."""

from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass
from typing import Any, Dict

import aiohttp

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

    # ------------------------------------------------------------------
    async def _get_async(self, path: str) -> Any:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.url}{path}",
                timeout=aiohttp.ClientTimeout(total=5.0),
            ) as resp:
                resp.raise_for_status()
                return await resp.json()

    async def _post_async(self, path: str, payload: Dict[str, Any]) -> Any:

        headers = {"Content-Type": "application/vnd.schemaregistry.v1+json"}
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.url}{path}",
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=5.0),
            ) as resp:
                resp.raise_for_status()
                return await resp.json()

    # Backwards compatible synchronous wrappers ------------------------
    def _get(self, path: str) -> Any:
        """Synchronous wrapper around :meth:`_get_async`."""
        return asyncio.run(self._get_async(path))

    def _post(self, path: str, payload: Dict[str, Any]) -> Any:
        """Synchronous wrapper around :meth:`_post_async`."""
        return asyncio.run(self._post_async(path, payload))

    # ------------------------------------------------------------------
    async def get_schema_async(
        self, subject: str, version: int | str = "latest"
    ) -> SchemaInfo:
        data = await self._get_async(f"/subjects/{subject}/versions/{version}")
        return SchemaInfo(
            id=data["id"], version=data["version"], schema=json.loads(data["schema"])
        )

    @lru_cache(maxsize=64)
    def get_schema(self, subject: str, version: int | str = "latest") -> SchemaInfo:
        return asyncio.run(self.get_schema_async(subject, version))

    async def get_schema_by_id_async(self, schema_id: int) -> SchemaInfo:
        data = await self._get_async(f"/schemas/ids/{schema_id}")
        return SchemaInfo(id=schema_id, version=-1, schema=json.loads(data["schema"]))

    @lru_cache(maxsize=64)
    def get_schema_by_id(self, schema_id: int) -> SchemaInfo:
        return asyncio.run(self.get_schema_by_id_async(schema_id))

    async def check_compatibility_async(
        self, subject: str, schema: Dict[str, Any], version: str = "latest"
    ) -> bool:
        data = await self._post_async(
            f"/compatibility/subjects/{subject}/versions/{version}",
            {"schema": json.dumps(schema)},
        )
        is_compatible = bool(data.get("is_compatible"))
        if not is_compatible:
            get_data_quality_monitor().record_compatibility_failure()
        return is_compatible

    def check_compatibility(
        self, subject: str, schema: Dict[str, Any], version: str = "latest"
    ) -> bool:
        return asyncio.run(self.check_compatibility_async(subject, schema, version))

    async def register_schema_async(self, subject: str, schema: Dict[str, Any]) -> int:
        """Register a new schema version under ``subject`` and return the version."""
        data = await self._post_async(
            f"/subjects/{subject}/versions",
            {"schema": json.dumps(schema)},
        )
        version = data.get("version")
        if version is None:
            versions = await self._get_async(f"/subjects/{subject}/versions")

            version = max(versions)

        # invalidate cached schema for this subject
        async with self._lock:
            self._schema_cache.pop((subject, str(version)), None)
            self._id_cache.pop(int(version), None)

        return int(version)

    def register_schema(self, subject: str, schema: Dict[str, Any]) -> int:
        return asyncio.run(self.register_schema_async(subject, schema))


__all__ = ["SchemaRegistryClient", "SchemaInfo"]
