from __future__ import annotations

import asyncpg
from asyncpg.utils import _quote_ident


class IntegrityChecker:
    """Validate table row counts between source and target."""

    async def rowcount_equal(
        self, source: asyncpg.Pool, target: asyncpg.Pool, table: str
    ) -> bool:
        safe_table = _quote_ident(table)
        query = f"SELECT COUNT(*) FROM {safe_table}"
        src = await source.fetchval(query)
        tgt = await target.fetchval(query)
        return src == tgt


__all__ = ["IntegrityChecker"]
