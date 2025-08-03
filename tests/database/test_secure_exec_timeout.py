import pytest

from database import secure_exec


class DummyOptimizer:
    def optimize_query(self, sql: str) -> str:
        return sql


class FakePGConn:
    def __init__(self):
        self._optimizer = DummyOptimizer()
        self.executed = []

    def execute(self, sql, params=None):
        self.executed.append((sql, params))
        return "ok"


class FakeSQLiteConn:
    __module__ = "sqlite3"

    def __init__(self):
        self._optimizer = DummyOptimizer()
        self.executed = []

    def execute(self, sql, params=None):
        self.executed.append((sql, params))
        if sql.startswith("SELECT"):
            raise TimeoutError("boom")
        return "ok"


def test_postgres_statement_timeout(monkeypatch):
    class DS:
        query_timeout_seconds = 1

    monkeypatch.setattr(secure_exec, "DatabaseSettings", DS)
    conn = FakePGConn()
    secure_exec.execute_query(conn, "SELECT 1")
    assert conn.executed[0][0] == "SET LOCAL statement_timeout = 1000"
    assert conn.executed[1][0] == "SELECT 1"
    assert conn.executed[2][0] == "SET LOCAL statement_timeout = DEFAULT"


def test_sqlite_busy_timeout_reset(monkeypatch):
    class DS:
        query_timeout_seconds = 2

    monkeypatch.setattr(secure_exec, "DatabaseSettings", DS)
    conn = FakeSQLiteConn()
    with pytest.raises(TimeoutError):
        secure_exec.execute_query(conn, "SELECT 1")
    assert conn.executed[0][0] == "PRAGMA busy_timeout = 2000"
    assert conn.executed[-1][0] == "PRAGMA busy_timeout = 0"
