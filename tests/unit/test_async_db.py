from __future__ import annotations

import asyncio
import importlib.util
from pathlib import Path

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


class StubRepo:
    def __init__(self, ok: bool = True) -> None:
        self.ok = ok
        self.called = False

    async def check(self) -> None:
        self.called = True
        if not self.ok:
            raise RuntimeError("fail")


def test_pool_creation(monkeypatch):
    class DummyPool:
        async def close(self) -> None:
            pass

    async def fake_create_pool(**_):
        return DummyPool()

    monkeypatch.setattr(async_db.asyncpg, "create_pool", fake_create_pool)
    pool = asyncio.run(async_db.create_pool("postgresql://"))
    assert isinstance(pool, DummyPool)
    asyncio.run(async_db.close_pool())


def test_health_check_with_repository():
    repo = StubRepo()
    assert asyncio.run(async_db.health_check(repo)) is True
    assert repo.called is True


def test_health_check_failure():
    repo = StubRepo(ok=False)
    assert asyncio.run(async_db.health_check(repo)) is False
