import pytest

from yosai_intel_dashboard.src.infrastructure.config.database_exceptions import (
    UnicodeEncodingError,
)
from yosai_intel_dashboard.src.infrastructure.security.secure_query_wrapper import (
    execute_secure_command,
    execute_secure_sql,
)


class DummyConn:
    def __init__(self):
        self.last = None

    def execute_query(self, query: str, params: tuple | None = None):
        self.last = (query, params)
        return [("ok",)]

    def execute_command(self, query: str, params: tuple | None = None):
        self.last = (query, params)
        return 1

    def execute_batch(self, command: str, params_seq):
        self.last = (command, list(params_seq))
        return 1


def test_execute_secure_sql_basic():
    conn = DummyConn()
    result = execute_secure_sql(conn, "SELECT 1 WHERE a=%s", ("b",))
    assert result == [("ok",)]
    assert conn.last == ("SELECT 1 WHERE a=%s", ("b",))


def test_injection_through_params():
    conn = DummyConn()
    execute_secure_sql(conn, "SELECT 1 WHERE a=%s", ("1 OR 1=1",))
    assert conn.last == ("SELECT 1 WHERE a=%s", ("1 OR 1=1",))


def test_surrogate_query_rejected():
    conn = DummyConn()
    bad_query = "SELECT '" + chr(0xD800) + "'"
    with pytest.raises(UnicodeEncodingError):
        execute_secure_sql(conn, bad_query)


def test_execute_secure_command():
    conn = DummyConn()
    result = execute_secure_command(conn, "DELETE FROM t WHERE id=%s", (1,))
    assert result == 1
    assert conn.last == ("DELETE FROM t WHERE id=%s", (1,))
