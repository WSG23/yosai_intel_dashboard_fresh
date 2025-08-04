from __future__ import annotations

import pytest

from yosai_intel_dashboard.src.core.exceptions import ValidationError
from yosai_intel_dashboard.src.database.secure_exec import (
    execute_command,
    execute_query,
)


class DummyConn:
    def execute_query(self, sql, params=None):
        raise AssertionError("execute_query should not be called on unsafe SQL")

    def execute(self, sql, params=None):
        raise AssertionError("execute should not be called on unsafe SQL")


def test_execute_query_injection_raises():
    conn = DummyConn()
    malicious = "SELECT 1; DROP TABLE users;"
    with pytest.raises(ValidationError) as excinfo:
        execute_query(conn, malicious)
    assert "parameterized" in str(excinfo.value)


def test_execute_command_injection_raises():
    conn = DummyConn()
    malicious = "DELETE FROM users; -- remove all"
    with pytest.raises(ValidationError) as excinfo:
        execute_command(conn, malicious)
    assert "parameterized" in str(excinfo.value)
