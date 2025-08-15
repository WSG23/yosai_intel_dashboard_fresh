import pytest

from yosai_intel_dashboard.src.infrastructure.config.database_exceptions import UnicodeEncodingError
from yosai_intel_dashboard.src.infrastructure.config.secure_db import execute_secure_query


class DummyConn:
    def __init__(self):
        self.called_with = None

    def execute_query(self, query: str, params: tuple | None = None):
        self.called_with = (query, params)
        return "ok"

    def execute_batch(self, command: str, params_seq):
        self.called_with = (command, list(params_seq))
        return "ok"


def test_execute_secure_query_basic():
    conn = DummyConn()
    result = execute_secure_query(conn, "SELECT 1", ("a",))
    assert result == "ok"
    assert conn.called_with == ("SELECT 1", ("a",))


def test_execute_secure_query_surrogate_query():
    conn = DummyConn()
    bad_query = "SELECT '" + chr(0xD800) + "'"
    with pytest.raises(UnicodeEncodingError):
        execute_secure_query(conn, bad_query)


def test_execute_secure_query_surrogate_params():
    conn = DummyConn()
    bad_param = "bad" + chr(0xDFFF)
    with pytest.raises(UnicodeEncodingError):
        execute_secure_query(conn, "SELECT 1", (bad_param,))
