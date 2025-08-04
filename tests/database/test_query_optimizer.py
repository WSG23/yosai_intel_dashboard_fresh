from __future__ import annotations

from yosai_intel_dashboard.src.database.query_optimizer import DatabaseQueryOptimizer
from yosai_intel_dashboard.src.database.secure_exec import execute_query


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
