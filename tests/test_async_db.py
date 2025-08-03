import asyncio
import importlib.util
from pathlib import Path
from typing import Any

import pytest

spec = importlib.util.spec_from_file_location(
    "async_db",
    Path(__file__).resolve().parents[1]
    / "yosai_intel_dashboard"
    / "src"
    / "services"
    / "common"
    / "async_db.py",
)
async_db = importlib.util.module_from_spec(spec)
spec.loader.exec_module(async_db)  # type: ignore


class DummyAcquireContext:
    def __init__(self, pool: "DummyPool") -> None:
        self.pool = pool

    def __await__(self):
        async def _acquire() -> "DummyPool":
            self.pool.acquired = True
            return self.pool

        return _acquire().__await__()

    async def __aenter__(self) -> "DummyPool":
        self.pool.acquired = True
        return self.pool

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.pool.release(self.pool)


class DummyPool:
    def __init__(self) -> None:
        self.acquired = False
        self.closed = False

    def acquire(self) -> DummyAcquireContext:  # type: ignore[override]
        return DummyAcquireContext(self)

    async def release(self, _conn: Any) -> None:
        self.acquired = False

    async def close(self) -> None:
        self.closed = True

    async def execute(self, _query: str) -> None:
        return None


def test_pool_creation(monkeypatch):
    created = {}

    async def fake_create_pool(**kwargs):
        created.update(kwargs)
        return DummyPool()

    monkeypatch.setattr(async_db.asyncpg, "create_pool", fake_create_pool)
    pool = asyncio.run(async_db.create_pool("postgresql://"))
    assert isinstance(pool, DummyPool)
    assert created["dsn"] == "postgresql://"
    asyncio.run(async_db.close_pool())


def test_health_check(monkeypatch):
    pool = DummyPool()

    async def fake_create_pool(**_):
        return pool

    monkeypatch.setattr(async_db.asyncpg, "create_pool", fake_create_pool)
    await async_db.create_pool("postgresql://")
    ok = await async_db.health_check()
    assert ok is True
    assert pool.acquired is False
    await async_db.close_pool()


@pytest.mark.asyncio
async def test_connection_cleanup_on_exception(monkeypatch):
    class BadPool(DummyPool):
        async def execute(self, _query: str):
            raise RuntimeError("fail")


    async def fake_create_pool(**_):
        return BadPool()

    monkeypatch.setattr(async_db.asyncpg, "create_pool", fake_create_pool)
    await async_db.create_pool("postgresql://")
    assert await async_db.health_check() is False
    # connection should be released even after failure
    pool = await async_db.get_pool()
    assert isinstance(pool, DummyPool)
    assert pool.acquired is False
    await async_db.close_pool()

