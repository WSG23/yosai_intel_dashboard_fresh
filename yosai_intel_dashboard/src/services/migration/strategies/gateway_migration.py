from __future__ import annotations

from typing import AsyncIterator, List

import asyncpg
from yosai_intel_dashboard.src.infrastructure.config.constants import MIGRATION_CHUNK_SIZE

from ..framework import MigrationStrategy


class GatewayMigration(MigrationStrategy):
    """Migrate gateway related tables."""

    TABLE = "gateway_logs"
    CHUNK_SIZE = MIGRATION_CHUNK_SIZE

    def __init__(self, target_dsn: str) -> None:
        super().__init__(self.TABLE, target_dsn)

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
