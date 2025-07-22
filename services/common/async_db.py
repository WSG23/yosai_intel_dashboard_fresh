from typing import Optional

import asyncpg

_pool: Optional[asyncpg.pool.Pool] = None


async def create_pool(
    dsn: str,
    *,
    min_size: int = 1,
    max_size: int = 10,
    timeout: float = 30.0,
) -> asyncpg.pool.Pool:
    """Create a global asyncpg pool if not already created."""
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            dsn=dsn,
            min_size=min_size,
            max_size=max_size,
            timeout=timeout,
        )
    return _pool


async def get_pool() -> asyncpg.pool.Pool:
    if _pool is None:
        raise RuntimeError("Pool has not been initialized")
    return _pool


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


async def health_check() -> bool:
    """Return True if the pool can successfully run a simple query."""
    if _pool is None:
        return False
    try:
        conn = await _pool.acquire()
        try:
            await conn.execute("SELECT 1")
        finally:
            await _pool.release(conn)
        return True
    except Exception:
        return False
