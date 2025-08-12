"""Database-backed analytics service with in-memory caching.

This module provides a small façade around a :class:`DatabaseManager`.  The
service validates connectivity before executing any analytics queries and keeps
results in a simple in-memory cache with an expiration TTL.  Individual queries
are executed via private asynchronous helpers which each handle their own
exceptions, returning fallback values instead of bubbling up errors.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Mapping
from typing import Any, Dict, List

from yosai_intel_dashboard.src.infrastructure.config.connection_pool import (
    DatabaseConnectionPool,
    DEFAULT_POOL_ACQUIRE_TIMEOUT,
)


class AnalyticsService:
    """Retrieve analytics information from the database.

    Parameters
    ----------
    pool:
        :class:`DatabaseConnectionPool` used to obtain database connections.
    ttl:
        Number of seconds analytics results remain cached.  Defaults to ``60``.
    acquire_timeout:
        Timeout when acquiring a connection from the pool.  Defaults to
        ``DEFAULT_POOL_ACQUIRE_TIMEOUT``.
    """

    def __init__(
        self,
        pool: DatabaseConnectionPool,
        ttl: int = 60,
        *,
        acquire_timeout: float | None = None,
    ) -> None:
        self._pool = pool
        self._ttl = ttl
        self._timeout = (
            acquire_timeout if acquire_timeout is not None else DEFAULT_POOL_ACQUIRE_TIMEOUT
        )
        self._cache: Dict[str, Any] | None = None
        self._expiry: float = 0.0

    # ------------------------------------------------------------------
    # Cache helpers
    # ------------------------------------------------------------------
    def _cache_valid(self) -> bool:
        return self._cache is not None and time.time() < self._expiry

    def _get_cached(self) -> Dict[str, Any] | None:
        return self._cache if self._cache_valid() else None

    def _set_cache(self, value: Dict[str, Any]) -> None:
        self._cache = value
        self._expiry = time.time() + self._ttl

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------
    async def _fetch_user_count(self, conn: Any) -> int:
        """Return number of users in the system.

        Any exceptions are swallowed and ``0`` is returned instead.
        """

        query = "SELECT COUNT(*) as count FROM users"
        try:
            rows = await asyncio.to_thread(conn.execute_query, query)
            if isinstance(rows, list) and rows:
                first = rows[0]
                if isinstance(first, Mapping):
                    return int(first.get("count", 0))
                if isinstance(first, (list, tuple)):
                    return int(first[0])
            return 0
        except Exception:
            return 0

    async def _fetch_recent_events(self, conn: Any) -> List[Mapping[str, Any]]:
        """Return recent event records.

        Any exceptions are swallowed and an empty list is returned instead.
        """

        query = (
            "SELECT event_type, status, timestamp "
            "FROM access_events ORDER BY timestamp DESC LIMIT 10"
        )
        try:
            rows = await asyncio.to_thread(conn.execute_query, query)
            if not rows:
                return []
            return list(rows)
        except Exception:
            return []

    async def _gather_analytics(self, conn: Any) -> Dict[str, Any]:
        user_count, recent_events = await asyncio.gather(
            self._fetch_user_count(conn),
            self._fetch_recent_events(conn),
        )
        return {"user_count": user_count, "recent_events": recent_events}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def get_analytics(self) -> Dict[str, Any]:
        """Return analytics data, using the cache when possible."""

        cached = self._get_cached()
        if cached is not None:
            return cached

        try:
            if not self._pool.health_check():
                return {
                    "status": "error",
                    "message": "database health check failed",
                    "error_code": "health_check_failed",
                }
            with self._pool.acquire(timeout=self._timeout) as connection:
                data = asyncio.run(self._gather_analytics(connection))
            result = {"status": "success", "data": data}
            self._set_cache(result)
            return result
        except TimeoutError as exc:
            return {
                "status": "error",
                "message": str(exc),
                "error_code": "pool_timeout",
            }
        except Exception as exc:  # pragma: no cover - best effort
            return {
                "status": "error",
                "message": str(exc),
                "error_code": "query_failed",
            }


__all__ = ["AnalyticsService"]
