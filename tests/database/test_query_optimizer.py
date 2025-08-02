from services.database.query_optimizer import DatabaseQueryOptimizer


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
