from __future__ import annotations

import asyncpg

from infrastructure.security.query_builder import SecureQueryBuilder


class IntegrityChecker:
    """Validate table row counts between source and target."""

    async def rowcount_equal(
        self, source: asyncpg.Pool, target: asyncpg.Pool, table: str
    ) -> bool:
        builder = SecureQueryBuilder(allowed_tables={table})
        tbl = builder.table(table)
        query, _ = builder.build("SELECT COUNT(*) FROM %s", tbl)
        src = await source.fetchval(query)
        tgt = await target.fetchval(query)
        return src == tgt


__all__ = ["IntegrityChecker"]
