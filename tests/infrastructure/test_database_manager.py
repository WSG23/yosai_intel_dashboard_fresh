from __future__ import annotations

import asyncio
import asyncpg
import pytest

from src.infrastructure.database.manager import DatabaseConfig, DatabaseManager


class DummyConnection:
    def __init__(self) -> None:
        self.queries = []
        self.commands = []

    async def fetch(self, query: str, *args):  # pragma: no cover - trivial
        self.queries.append((query, args))
        return ["ok"]

    async def execute(self, command: str, *args):  # pragma: no cover - trivial
        self.commands.append((command, args))
        return "EXEC"


class DummyPool:
    def __init__(self) -> None:
        self.connection = DummyConnection()
        self.closed = False

    async def close(self) -> None:  # pragma: no cover - trivial
        self.closed = True

    def acquire(self):  # pragma: no cover - trivial
        pool = self

        class _AcquireContext:
            async def __aenter__(self):
                return pool.connection

            async def __aexit__(self, exc_type, exc, tb):
                return False

        return _AcquireContext()


def test_database_manager_success(monkeypatch):
    async def run() -> None:
        pool = DummyPool()

        async def fake_create_pool(**kwargs):
            return pool

        monkeypatch.setattr(asyncpg, "create_pool", fake_create_pool)

        config = DatabaseConfig(
            host="localhost",
            port=5432,
            database="db",
            username="user",
            password="pass",
            min_connections=1,
            max_connections=5,
            timeout=10.0,
        )
        manager = DatabaseManager(config)
        await manager.initialize()

        res = await manager.execute_query("SELECT 1")
        assert res == ["ok"]
        cmd_res = await manager.execute_command("UPDATE x")
        assert cmd_res == "EXEC"
        assert await manager.health_check() is True
        assert manager.is_healthy is True

        await manager.close()
        assert pool.closed is True

    asyncio.run(run())


def test_initialize_failure(monkeypatch, caplog):
    async def run() -> None:
        async def fake_create_pool(**kwargs):
            raise RuntimeError("boom")

        monkeypatch.setattr(asyncpg, "create_pool", fake_create_pool)

        config = DatabaseConfig(
            host="localhost",
            port=5432,
            database="db",
            username="user",
            password="pass",
            min_connections=1,
            max_connections=5,
            timeout=10.0,
        )
        manager = DatabaseManager(config)

        with pytest.raises(RuntimeError):
            await manager.initialize()
        assert manager.is_healthy is False
        assert "Failed to initialize database pool" in caplog.text

    asyncio.run(run())
