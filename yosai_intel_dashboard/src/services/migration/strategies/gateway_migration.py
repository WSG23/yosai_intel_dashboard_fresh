from __future__ import annotations

from typing import AsyncIterator, List, Callable, Awaitable

import asyncpg
import logging
from infrastructure.database.secure_query import SecureQueryBuilder
from yosai_intel_dashboard.src.infrastructure.config.constants import MIGRATION_CHUNK_SIZE

from ..framework import MigrationStrategy

LOG = logging.getLogger(__name__)


class GatewayMigration(MigrationStrategy):
    """Migrate gateway related tables."""

    TABLE = "gateway_logs"
    CHUNK_SIZE = MIGRATION_CHUNK_SIZE

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
        builder = SecureQueryBuilder(allowed_tables={self.TABLE})
        table = builder.table(self.TABLE)
        while True:
            select_sql, params = builder.build(
                f"SELECT * FROM {table} OFFSET $1 LIMIT $2",
                (start, self.CHUNK_SIZE),
                logger=LOG,
            )
            rows: List[asyncpg.Record] = await source_pool.fetch(select_sql, *params)
            if not rows:
                break
            insert_sql, _ = builder.build(
                f"INSERT INTO {table} VALUES($1:record)", logger=LOG
            )
            await self.target_pool.executemany(insert_sql, rows)
            start += len(rows)
            yield len(rows)
