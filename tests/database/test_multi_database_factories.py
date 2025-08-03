from __future__ import annotations

import importlib.util
import pathlib
import sqlite3

import tests.config  # noqa: F401

# Load DatabaseConnectionPool without importing package __init__
_spec = importlib.util.spec_from_file_location(
    "connection_pool",
    pathlib.Path("yosai_intel_dashboard/src/infrastructure/config/connection_pool.py"),
)
_connection_pool = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_connection_pool)
DatabaseConnectionPool = _connection_pool.DatabaseConnectionPool


class SQLiteConn:
    def __init__(self) -> None:
        self._conn = sqlite3.connect(":memory:")

    def execute_query(self, query: str, params: tuple | None = None) -> list:
        return []

    def execute_command(self, command: str, params: tuple | None = None) -> None:
        pass

    def health_check(self) -> bool:
        return True

    def close(self) -> None:
        self._conn.close()


class DummyPostgres:
    def __init__(self) -> None:
        self.closed = False

    def execute_query(self, query: str, params: tuple | None = None) -> list:
        return []

    def execute_command(self, command: str, params: tuple | None = None) -> None:
        pass

    def health_check(self) -> bool:
        return True

    def close(self) -> None:
        self.closed = True


def sqlite_factory() -> SQLiteConn:
    return SQLiteConn()


def postgres_factory() -> DummyPostgres:
    return DummyPostgres()


def test_separate_pools_isolated():
    sqlite_pool = DatabaseConnectionPool(
        sqlite_factory, initial_size=1, max_size=2, timeout=1, shrink_timeout=1
    )
    postgres_pool = DatabaseConnectionPool(
        postgres_factory, initial_size=1, max_size=2, timeout=1, shrink_timeout=1
    )

    sqlite_conn = sqlite_pool.get_connection()
    pg_conn = postgres_pool.get_connection()

    assert isinstance(sqlite_conn, SQLiteConn)
    assert isinstance(pg_conn, DummyPostgres)

    sqlite_pool.release_connection(sqlite_conn)
    postgres_pool.release_connection(pg_conn)

    assert all(isinstance(c, SQLiteConn) for c, _ in sqlite_pool._pool)
    assert all(isinstance(c, DummyPostgres) for c, _ in postgres_pool._pool)
