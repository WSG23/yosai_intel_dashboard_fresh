from __future__ import annotations

from typing import AsyncIterator, List, Callable, Awaitable

import asyncpg
from yosai_intel_dashboard.src.infrastructure.config.constants import DataProcessingLimits

from ..framework import MigrationStrategy


class EventsMigration(MigrationStrategy):
    """Migrate access events table. Supports TimescaleDB targets."""

    TABLE = "access_events"
    CHUNK_SIZE = DataProcessingLimits.DEFAULT_QUERY_LIMIT

    def __init__(
        self,
        target_dsn: str,
        *,
        pool_factory: Callable[..., Awaitable[asyncpg.Pool]] | None = None,
    ) -> None:
        super().__init__(self.TABLE, target_dsn, pool_factory=pool_factory)

    async def run(self, source_pool: asyncpg.Pool) -> AsyncIterator[int]:
        start = 0
        assert self.target_pool is not None
        while True:
            rows: List[asyncpg.Record] = await source_pool.fetch(
                f"SELECT * FROM {self.TABLE} OFFSET $1 LIMIT $2",
                start,
                self.CHUNK_SIZE,
            )
            if not rows:
                break
            await self.target_pool.executemany(
                f"INSERT INTO {self.TABLE} VALUES($1:record)", rows
            )
            start += len(rows)
            yield len(rows)
