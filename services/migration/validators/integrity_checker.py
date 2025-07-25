from __future__ import annotations

import asyncpg


class IntegrityChecker:
    """Validate table row counts between source and target."""

    async def rowcount_equal(
        self, source: asyncpg.Pool, target: asyncpg.Pool, table: str
    ) -> bool:
        src = await source.fetchval(f"SELECT COUNT(*) FROM {table}")
        tgt = await target.fetchval(f"SELECT COUNT(*) FROM {table}")
        return src == tgt


__all__ = ["IntegrityChecker"]
