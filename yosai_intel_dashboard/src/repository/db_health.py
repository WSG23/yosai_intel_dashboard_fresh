"""Database health check repository."""
from __future__ import annotations

from typing import Protocol

import asyncpg


class DBHealthRepository(Protocol):
    """Check database connectivity."""

    async def check(self) -> None: ...


class PoolDBHealthRepository(DBHealthRepository):
    """Run a simple query using an asyncpg pool."""

    def __init__(self, pool: asyncpg.pool.Pool) -> None:
        self._pool = pool

    async def check(self) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute("SELECT 1")
