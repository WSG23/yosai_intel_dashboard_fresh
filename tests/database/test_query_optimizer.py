from __future__ import annotations

from yosai_intel_dashboard.src.database.query_optimizer import DatabaseQueryOptimizer
from yosai_intel_dashboard.src.database.secure_exec import execute_query
import pytest
import sys
import types


@pytest.fixture(autouse=True)
def stub_unicode_processor(monkeypatch: pytest.MonkeyPatch) -> None:
    class StubProcessor:
        @staticmethod
        def encode_query(query: str) -> str:
            return query

    module = types.SimpleNamespace(UnicodeSQLProcessor=StubProcessor)
    monkeypatch.setitem(sys.modules, "yosai_intel_dashboard.src.core.unicode", module)


def test_postgresql_hint_injection_and_cache():
    optimizer = DatabaseQueryOptimizer("postgresql")
    query = "SELECT * FROM items"
    optimized1 = optimizer.optimize_query(query)
    assert optimized1.startswith("/*+ Parallel */")
    optimized2 = optimizer.optimize_query(query)
    assert optimized1 is optimized2


def test_sqlite_hint_injection():
    optimizer = DatabaseQueryOptimizer("sqlite")
    query = "SELECT * FROM items"
    optimized = optimizer.optimize_query(query)
    assert optimized.startswith("/*+ NO_INDEX */")


def test_execute_query_uses_optimizer_and_handles_unicode():
    class Recorder:
        def __init__(self):
            self.sql = None

        def execute(self, sql, params=None):  # type: ignore[no-untyped-def]
            self.sql = sql
            return []

    conn = Recorder()
    execute_query(conn, "SELECT '😀'")
    assert conn.sql is not None
    assert conn.sql.startswith("/*+ Parallel */")
    assert "😀" in conn.sql


@pytest.mark.parametrize("db_type", ["postgresql", "sqlite"])
def test_hint_injection_disabled(db_type: str) -> None:
    optimizer = DatabaseQueryOptimizer(db_type, enable_hints=False)
    query = "SELECT * FROM items"
    optimized = optimizer.optimize_query(query)
    assert not optimized.startswith("/*+")
    assert optimized == query
