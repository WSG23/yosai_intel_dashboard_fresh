"""Asynchronous database manager supporting multiple drivers."""

from __future__ import annotations

import logging
from typing import Any, Optional

from yosai_intel_dashboard.src.database.async_engine_factory import get_asyncpg_driver
from yosai_intel_dashboard.src.infrastructure.config.constants import (
    DEFAULT_DB_HOST,
    DEFAULT_DB_PORT,
)
from yosai_intel_dashboard.src.infrastructure.monitoring.performance_profiler import (
    PerformanceProfiler,
)

logger = logging.getLogger(__name__)


class AsyncPostgreSQLManager:
    """Simplified async database manager with pluggable drivers."""

    def __init__(self, config: Any) -> None:
        self.config = config
        self.pool: Optional[Any] = None
        self.driver = get_asyncpg_driver()
        self._profiler = PerformanceProfiler()

    async def create_pool(self) -> Any:
        if self.pool is None:
            if self.driver == "asyncpg":
                import asyncpg

                self.pool = await asyncpg.create_pool(
                    host=getattr(self.config, "host", DEFAULT_DB_HOST),
                    port=getattr(self.config, "port", DEFAULT_DB_PORT),
                    database=getattr(self.config, "name", "postgres"),
                    user=getattr(self.config, "user", "postgres"),
                    password=getattr(self.config, "password", ""),
                    min_size=getattr(self.config, "initial_pool_size", 1),
                    max_size=getattr(self.config, "max_pool_size", 10),
                    timeout=getattr(self.config, "connection_timeout", 30),
                )
            else:  # psycopg async pool
                from psycopg_pool import AsyncConnectionPool

                conninfo = (
                    f"postgresql://{getattr(self.config, 'user', 'postgres')}:"
                    f"{getattr(self.config, 'password', '')}@"
                    f"{getattr(self.config, 'host', DEFAULT_DB_HOST)}:"
                    f"{getattr(self.config, 'port', DEFAULT_DB_PORT)}/"
                    f"{getattr(self.config, 'name', 'postgres')}"
                )
                self.pool = AsyncConnectionPool(
                    conninfo,
                    min_size=getattr(self.config, "initial_pool_size", 1),
                    max_size=getattr(self.config, "max_pool_size", 10),
                    timeout=getattr(self.config, "connection_timeout", 30),
                )
        return self.pool

    async def execute(self, query: str, *params: Any) -> Any:
        pool = await self.create_pool()
        async with self._profiler.track_db_query(query):
            if self.driver == "asyncpg":
                async with pool.acquire() as conn:
                    return await conn.fetch(query, *params)
            async with pool.connection() as conn:  # psycopg
                async with conn.cursor() as cur:
                    await cur.execute(query, params or None)
                    return await cur.fetchall()

    async def health_check(self) -> bool:
        try:
            pool = await self.create_pool()
            if self.driver == "asyncpg":
                async with pool.acquire() as conn:
                    await conn.execute("SELECT 1")
            else:
                async with pool.connection() as conn:
                    async with conn.cursor() as cur:
                        await cur.execute("SELECT 1")
            return True
        except Exception as exc:  # pragma: no cover - best effort
            logger.warning(f"Async DB health check failed: {exc}")
            return False

    async def close(self) -> None:
        if self.pool is not None:
            await self.pool.close()
            self.pool = None


__all__ = ["AsyncPostgreSQLManager"]
