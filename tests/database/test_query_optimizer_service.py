from services.query_optimizer import QueryOptimizer


class FakeConn:
    def execute_query(self, sql, params=None):
        if sql.startswith("EXPLAIN"):
            return [{"detail": "SCAN TABLE items"}]
        if "COUNT(DISTINCT name)" in sql:
            return [{"distinct": 3, "total": 10}]
        return []


def test_suggest_indexes_from_plan():
    optimizer = QueryOptimizer(FakeConn())
    suggestions = optimizer.suggest_indexes("SELECT * FROM items WHERE name='a'")
    assert suggestions == ["CREATE INDEX idx_items_name ON items (name)"]
