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


class DummyPool:
    def __init__(self) -> None:
        self.acquired = False
        self.closed = False

    async def acquire(self) -> "DummyPool":  # type: ignore[override]
        self.acquired = True
        return self

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.release(self)

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

    async def run():
        monkeypatch.setattr(async_db.asyncpg, "create_pool", fake_create_pool)
        await async_db.create_pool("postgresql://")
        ok = await async_db.health_check()
        assert isinstance(ok, async_db.DBHealthStatus)
        assert ok.healthy is True
        await async_db.close_pool()

    asyncio.run(run())


def test_health_check_failure(monkeypatch):
    async def fake_create_pool(**_):
        class BadPool(DummyPool):
            async def execute(self, _query: str):
                raise RuntimeError("fail")

            async def acquire(self):
                return self

        return BadPool()

    async def run():
        monkeypatch.setattr(async_db.asyncpg, "create_pool", fake_create_pool)
        await async_db.create_pool("postgresql://")
        assert (await async_db.health_check()).healthy is False
        await async_db.close_pool()

    asyncio.run(run())
