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


class FakePGConnNoParam(FakePGConn):
    def execute(self, sql, params=None):
        if params is not None:
            raise TypeError("no params")
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


class FakeSQLiteConnNoParam:
    __module__ = "sqlite3"

    def __init__(self):
        self._optimizer = DummyOptimizer()
        self.executed = []

    def execute(self, sql, params=None):
        if params is not None:
            raise TypeError("no params")
        self.executed.append((sql, params))
        return "ok"


def test_postgres_statement_timeout(monkeypatch):
    class DS:
        query_timeout_seconds = 1

    monkeypatch.setattr(secure_exec, "DatabaseSettings", DS)
    conn = FakePGConn()
    secure_exec.execute_query(conn, "SELECT 1")
    assert conn.executed[0] == ("SET LOCAL statement_timeout = %s", (1000,))
    assert conn.executed[1] == ("SELECT 1", None)
    assert conn.executed[2] == ("SET LOCAL statement_timeout = DEFAULT", None)


def test_sqlite_busy_timeout_reset(monkeypatch):
    class DS:
        query_timeout_seconds = 2

    monkeypatch.setattr(secure_exec, "DatabaseSettings", DS)
    conn = FakeSQLiteConn()
    with pytest.raises(TimeoutError):
        secure_exec.execute_query(conn, "SELECT 1")
    assert conn.executed[0] == ("PRAGMA busy_timeout = ?", (2000,))
    assert conn.executed[-1] == ("PRAGMA busy_timeout = 0", None)


def test_postgres_statement_timeout_no_param_support(monkeypatch):
    class DS:
        query_timeout_seconds = 1

    monkeypatch.setattr(secure_exec, "DatabaseSettings", DS)
    conn = FakePGConnNoParam()
    secure_exec.execute_query(conn, "SELECT 1")
    assert conn.executed[0] == ("SET LOCAL statement_timeout = 1000", None)
    assert conn.executed[1] == ("SELECT 1", None)
    assert conn.executed[2] == ("SET LOCAL statement_timeout = DEFAULT", None)


def test_sqlite_busy_timeout_no_param_support(monkeypatch):
    class DS:
        query_timeout_seconds = 1

    monkeypatch.setattr(secure_exec, "DatabaseSettings", DS)
    conn = FakeSQLiteConnNoParam()
    secure_exec.execute_query(conn, "SELECT 1")
    assert conn.executed[0] == ("PRAGMA busy_timeout = 1000", None)
    assert conn.executed[1] == ("SELECT 1", None)
    assert conn.executed[2] == ("PRAGMA busy_timeout = 0", None)
