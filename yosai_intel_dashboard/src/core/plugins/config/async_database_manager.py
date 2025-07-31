"""Asynchronous database manager using asyncpg."""

from __future__ import annotations

import logging
from typing import Any, Optional

import asyncpg

from yosai_intel_dashboard.src.infrastructure.config.constants import DEFAULT_DB_HOST, DEFAULT_DB_PORT

logger = logging.getLogger(__name__)


class AsyncPostgreSQLManager:
    """Simplified async database manager relying on ``asyncpg``."""

    def __init__(self, config: Any):
        self.config = config
        self.pool: Optional[asyncpg.Pool] = None

    async def create_pool(self) -> asyncpg.Pool:
        if self.pool is None:
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
        return self.pool

    async def execute(self, query: str, *params: Any) -> Any:
        pool = await self.create_pool()
        async with pool.acquire() as conn:
            return await conn.fetch(query, *params)

    async def health_check(self) -> bool:
        try:
            pool = await self.create_pool()
            async with pool.acquire() as conn:
                await conn.execute("SELECT 1")
            return True
        except Exception as exc:  # pragma: no cover - best effort
            logger.warning(f"Async DB health check failed: {exc}")
            return False

    async def close(self) -> None:
        if self.pool is not None:
            await self.pool.close()
            self.pool = None


__all__ = ["AsyncPostgreSQLManager"]
