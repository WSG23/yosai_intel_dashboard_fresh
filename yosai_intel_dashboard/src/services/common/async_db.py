from __future__ import annotations

import asyncio
import logging
from typing import Optional

import asyncpg

from factories.db_health import DBHealthStatus


_pool: Optional[asyncpg.pool.Pool] = None


async def create_pool(
    dsn: str,
    *,
    min_size: int = 1,
    max_size: int = 10,
    timeout: float = 30.0,
    max_retries: int = 3,
    backoff: float = 0.5,
) -> asyncpg.pool.Pool:
    """Create a global asyncpg pool if not already created with retries."""

    global _pool
    if _pool is not None:
        return _pool

    attempt = 0
    delay = backoff
    log = logging.getLogger(__name__)
    while True:
        try:
            _pool = await asyncpg.create_pool(
                dsn=dsn,
                min_size=min_size,
                max_size=max_size,
                timeout=timeout,
            )
            return _pool
        except Exception as exc:  # pragma: no cover - network failures
            attempt += 1
            log.error("Async pool connection failed (attempt %s): %s", attempt, exc)
            if attempt >= max_retries:
                raise
            await asyncio.sleep(delay)
            delay *= 2


async def get_pool() -> asyncpg.pool.Pool:
    if _pool is None:
        raise RuntimeError("Pool has not been initialized")
    return _pool


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


async def health_check() -> DBHealthStatus:
    """Run a simple query to determine database health."""
    if _pool is None:
        return DBHealthStatus(healthy=False, details={"error": "pool not initialized"})
    try:
        conn = await _pool.acquire()
        try:
            await conn.execute("SELECT 1")
        finally:
            await _pool.release(conn)
        return DBHealthStatus(healthy=True, details={})
    except Exception as exc:  # pragma: no cover - safety net
        return DBHealthStatus(healthy=False, details={"error": str(exc)})
