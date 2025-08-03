import pytest
import importlib.util
from pathlib import Path

spec_cp = importlib.util.spec_from_file_location(
    "connection_pool",
    Path(__file__).resolve().parents[1]
    / "yosai_intel_dashboard"
    / "src"
    / "infrastructure"
    / "config"
    / "connection_pool.py",
)
cp_module = importlib.util.module_from_spec(spec_cp)
spec_cp.loader.exec_module(cp_module)  # type: ignore
DatabaseConnectionPool = cp_module.DatabaseConnectionPool


class MockConnection:
    def __init__(self):
        self._connected = True

    def execute_query(self, query, params=None):
        return []

    def execute_command(self, command, params=None):
        return None

    def health_check(self):
        return self._connected

    def close(self):
        self._connected = False


def factory():
    return MockConnection()


def test_acquire_timeout():
    pool = DatabaseConnectionPool(factory, 1, 1, timeout=0.1, shrink_timeout=1)
    conn = pool.get_connection()
    with pytest.raises(TimeoutError):
        with pool.acquire(timeout=0.1):
            pass
    pool.release_connection(conn)


def test_acquire_async_timeout():
    pool = DatabaseConnectionPool(factory, 1, 1, timeout=0.1, shrink_timeout=1)
    conn = pool.get_connection()

    async def attempt():
        async with pool.acquire_async(timeout=0.1):
            pass

    with pytest.raises(TimeoutError):
        import asyncio
        asyncio.run(attempt())
    pool.release_connection(conn)

