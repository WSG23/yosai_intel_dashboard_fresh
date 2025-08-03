"""Simplified Schema Registry client using HTTP requests."""

from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Tuple

import aiohttp

from monitoring.data_quality_monitor import get_data_quality_monitor
from yosai_intel_dashboard.src.core.async_utils.async_circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpen,
)
from yosai_intel_dashboard.src.error_handling.core import ErrorHandler
from yosai_intel_dashboard.src.error_handling.exceptions import ErrorCategory



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
        self._circuit_breaker = CircuitBreaker(5, 30, name="schema_registry")

        self._error_handler = ErrorHandler()

    # ------------------------------------------------------------------
    async def _get_async(self, path: str) -> Any:
        try:
            async with self._circuit_breaker:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{self.url}{path}",
                        timeout=aiohttp.ClientTimeout(total=5.0),
                    ) as resp:
                        resp.raise_for_status()
                        return await resp.json()
        except CircuitBreakerOpen as exc:
            self._error_handler.handle(exc, ErrorCategory.UNAVAILABLE)
            raise

    async def _post_async(self, path: str, payload: Dict[str, Any]) -> Any:
        headers = {"Content-Type": "application/vnd.schemaregistry.v1+json"}
        try:
            async with self._circuit_breaker:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.url}{path}",
                        json=payload,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=5.0),
                    ) as resp:
                        resp.raise_for_status()
                        return await resp.json()
        except CircuitBreakerOpen as exc:
            self._error_handler.handle(exc, ErrorCategory.UNAVAILABLE)
            raise

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
        key = (subject, str(version))
        async with self._lock:
            cached = self._schema_cache.get(key)
            if cached is not None:
                return cached

        for attempt in range(self._retries):
            try:
                async with self._cb:
                    data = await self._get_async(
                        f"/subjects/{subject}/versions/{version}"
                    )
                info = SchemaInfo(
                    id=data["id"],
                    version=data["version"],
                    schema=json.loads(data["schema"]),
                )
                async with self._lock:
                    self._schema_cache[key] = info
                    self._id_cache[info.id] = info
                return info
            except CircuitBreakerOpen as exc:
                self._error_handler.handle(exc, ErrorCategory.UNAVAILABLE)
                if cached is not None:
                    return cached
                raise
            except Exception as exc:
                self._error_handler.handle(exc, ErrorCategory.UNAVAILABLE)
                if attempt + 1 == self._retries:
                    if cached is not None:
                        return cached
                    raise
                await asyncio.sleep(0.1 * (attempt + 1))

        return cached  # pragma: no cover - loop exit

    def get_schema(self, subject: str, version: int | str = "latest") -> SchemaInfo:
        return asyncio.run(self.get_schema_async(subject, version))

    async def get_schema_by_id_async(self, schema_id: int) -> SchemaInfo:
        async with self._lock:
            cached = self._id_cache.get(schema_id)
            if cached is not None:
                return cached

        for attempt in range(self._retries):
            try:
                async with self._cb:
                    data = await self._get_async(f"/schemas/ids/{schema_id}")
                info = SchemaInfo(
                    id=schema_id,
                    version=-1,
                    schema=json.loads(data["schema"]),
                )
                async with self._lock:
                    self._id_cache[schema_id] = info
                return info
            except CircuitBreakerOpen as exc:
                self._error_handler.handle(exc, ErrorCategory.UNAVAILABLE)
                if cached is not None:
                    return cached
                raise
            except Exception as exc:
                self._error_handler.handle(exc, ErrorCategory.UNAVAILABLE)
                if attempt + 1 == self._retries:
                    if cached is not None:
                        return cached
                    raise
                await asyncio.sleep(0.1 * (attempt + 1))

        return cached  # pragma: no cover

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
