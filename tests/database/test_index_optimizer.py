from services.database.index_optimizer import IndexOptimizer


def make_sqlite_conn(indexes=None):
    class SQLiteConnection:
        def __init__(self, idx=None):
            self.indexes = idx or []
            self.executed = []

        def execute_query(self, query, params=None):
            self.executed.append((query, params))
            if query.startswith("PRAGMA index_list"):
                return [{"name": name} for name in self.indexes]
            if "sqlite_stat1" in query:
                return [{"index_name": name, "stat": "usage"} for name in self.indexes]
            return []

        def execute_command(self, command, params=None):
            self.executed.append((command, params))

    return SQLiteConnection(indexes)


def test_recommend_new_index():
    conn = make_sqlite_conn(["idx_existing"])
    opt = IndexOptimizer(conn)
    stmts = opt.recommend_new_indexes("tbl", ["col1", "col2"])
    assert stmts == ["CREATE INDEX idx_tbl_col1_col2 ON tbl (col1, col2)"]


def test_analyze_index_usage_handles_error():
    class BadConn:
        __name__ = "SQLiteConnection"

        def execute_query(self, query, params=None):
            raise RuntimeError("boom")

    opt = IndexOptimizer(BadConn())
    assert opt.analyze_index_usage() == []


class PostgreSQLConnection:

    def __init__(self):
        self.queries = []

    def execute_query(self, query, params=None):
        self.queries.append((query, params))
        if "pg_stat_user_indexes" in query:
            return [
                {
                    "index_name": "idx_tbl_col1",
                    "idx_scan": 1,
                    "idx_tup_read": 2,
                    "idx_tup_fetch": 3,
                }
            ]
        if "pg_indexes" in query:
            return [{"indexname": "idx_tbl_col1_col2"}]
        return []


def test_postgres_usage_and_recommend(monkeypatch):
    conn = PostgreSQLConnection()
    opt = IndexOptimizer(conn)
    stats = opt.analyze_index_usage()
    assert stats and stats[0]["index_name"] == "idx_tbl_col1"
    stmts = opt.recommend_new_indexes("tbl", ["col1", "col2"])
    assert not stmts  # index already exists
