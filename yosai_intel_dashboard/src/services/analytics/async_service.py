from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Protocol

import asyncpg

from yosai_intel_dashboard.src.core.cache_manager import CacheConfig, RedisCacheManager
from yosai_intel_dashboard.src.core.error_handling import with_async_error_handling

from .common_queries import fetch_access_patterns, fetch_dashboard_summary


class AsyncAnalyticsRepository(Protocol):
    """Protocol for asynchronous analytics data access."""

    pool: asyncpg.Pool

    async def fetch_dashboard_summary(
        self, conn: asyncpg.Connection, days: int = 7
    ) -> Dict[str, Any]:
        """Return dashboard summary for the given timeframe."""

    async def fetch_access_patterns(
        self, conn: asyncpg.Connection, days: int = 7
    ) -> Dict[str, Any]:
        """Return access pattern statistics."""


logger = logging.getLogger(__name__)


class PGAnalyticsRepository:
    """Default repository using :mod:`asyncpg` and shared queries."""

    def __init__(self, pool: asyncpg.Pool) -> None:
        self.pool = pool

    async def fetch_dashboard_summary(
        self, conn: asyncpg.Connection, days: int = 7
    ) -> Dict[str, Any]:
        return await fetch_dashboard_summary(conn, days)

    async def fetch_access_patterns(
        self, conn: asyncpg.Connection, days: int = 7
    ) -> Dict[str, Any]:
        return await fetch_access_patterns(conn, days)


class AsyncAnalyticsService:
    """Provide concurrent analytics calculations using asyncpg and Redis."""

    def __init__(
        self,
        repository: AsyncAnalyticsRepository,
        cache_manager: RedisCacheManager | None = None,
        *,
        cache_ttl: int = 300,
    ) -> None:
        self.repo = repository
        self.cache = cache_manager or RedisCacheManager(CacheConfig())
        self.cache_ttl = cache_ttl

    async def start(self) -> None:
        """Initialize cache resources."""
        await self.cache.start()

    async def stop(self) -> None:
        """Release cache resources."""
        await self.cache.stop()

    # ------------------------------------------------------------------
    @with_async_error_handling(reraise=True)
    async def get_dashboard_summary(self, days: int = 7) -> Dict[str, Any]:
        """Return dashboard summary using caching."""
        key = f"dashboard_summary:{days}"
        async with self.cache.get_lock(key):
            cached = await self.cache.get(key)
            if cached is not None:
                return cached
            async with self.repo.pool.acquire() as conn:
                result = await self.repo.fetch_dashboard_summary(conn, days)
            await self.cache.set(key, result, self.cache_ttl)
            return result

    @with_async_error_handling(reraise=True)
    async def get_access_patterns(self, days: int = 7) -> Dict[str, Any]:
        """Return access pattern statistics with caching."""
        key = f"access_patterns:{days}"
        async with self.cache.get_lock(key):
            cached = await self.cache.get(key)
            if cached is not None:
                return cached
            async with self.repo.pool.acquire() as conn:
                result = await self.repo.fetch_access_patterns(conn, days)
            await self.cache.set(key, result, self.cache_ttl)
            return result

    async def _combined_analytics(self, days: int = 7) -> Dict[str, Any]:
        async with (
            self.repo.pool.acquire() as conn1,
            self.repo.pool.acquire() as conn2,
        ):
            summary_task = self.repo.fetch_dashboard_summary(conn1, days)
            patterns_task = self.repo.fetch_access_patterns(conn2, days)
            summary, patterns = await asyncio.gather(summary_task, patterns_task)
        return {"summary": summary, "patterns": patterns}

    @with_async_error_handling(reraise=True)
    async def _combined_analytics_safe(self, days: int = 7) -> Dict[str, Any]:
        return await self._combined_analytics(days)

    async def get_combined_analytics(self, days: int = 7) -> Dict[str, Any]:
        """Return summary and pattern analytics concurrently."""
        try:
            return await self._combined_analytics_safe(days)
        except Exception as exc:  # pragma: no cover - runtime failures
            return {"status": "error", "message": str(exc)}


__all__ = [
    "AsyncAnalyticsService",
    "AsyncAnalyticsRepository",
    "PGAnalyticsRepository",
]
