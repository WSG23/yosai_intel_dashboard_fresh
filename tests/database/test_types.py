from __future__ import annotations

from typing import assert_type

from database.types import DBRow, DBRows


# Stub heavy dependencies to avoid circular imports during test collection
import sys
import types

dummy_conn = types.ModuleType("database.connection")


def _create_dummy_conn():
    class _Dummy:
        def execute_query(self, *args, **kwargs):
            return []

        def execute_command(self, *args, **kwargs):
            return None

        def execute_batch(self, *args, **kwargs):
            return None

        def health_check(self) -> bool:  # pragma: no cover - simple stub
            return True

    return _Dummy()


dummy_conn.create_database_connection = _create_dummy_conn
sys.modules.setdefault("database.connection", dummy_conn)

from yosai_intel_dashboard.src.infrastructure.config.database_manager import (
    MockConnection,
    SQLiteConnection,
)
from yosai_intel_dashboard.src.infrastructure.config.schema import DatabaseSettings


def test_mock_connection_returns_dbrows() -> None:
    conn = MockConnection()
    rows = conn.execute_query("SELECT 1")
    assert isinstance(rows, list)
    assert rows and isinstance(rows[0], dict)
    assert_type(rows, DBRows)
    assert_type(rows[0], DBRow)


def test_sqlite_connection_returns_dbrows(tmp_path) -> None:
    cfg = DatabaseSettings(name=str(tmp_path / "test.db"), type="sqlite")
    conn = SQLiteConnection(cfg)
    conn.execute_command("CREATE TABLE test (id INTEGER)")
    conn.execute_command("INSERT INTO test (id) VALUES (1)")
    rows = conn.execute_query("SELECT id FROM test")
    assert rows == [{"id": 1}]
    assert_type(rows, DBRows)
    assert_type(rows[0], DBRow)
