from yosai_intel_dashboard.src.database.index_optimizer import IndexOptimizer
from yosai_intel_dashboard.src.database import index_optimizer as idx_mod


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

        def execute_batch(self, command, params_seq):
            self.executed.append((command, list(params_seq)))

    return SQLiteConnection(indexes)


def test_recommend_new_index(monkeypatch):
    conn = make_sqlite_conn(["idx_existing"])
    monkeypatch.setattr(idx_mod, "execute_query", lambda c, q, p=None: c.execute_query(q, p))
    monkeypatch.setattr(idx_mod, "execute_command", lambda c, q, p=None: c.execute_command(q, p))
    opt = IndexOptimizer(conn)
    stmts = opt.recommend_new_indexes("tbl", ["col1", "col2"])
    assert stmts == ["CREATE INDEX idx_tbl_col1_col2 ON tbl (col1, col2)"]


def test_analyze_index_usage_handles_error(monkeypatch):
    class BadConn:
        __name__ = "SQLiteConnection"

        def execute_query(self, query, params=None):
            raise RuntimeError("boom")

    monkeypatch.setattr(idx_mod, "execute_query", lambda c, q, p=None: c.execute_query(q, p))
    monkeypatch.setattr(idx_mod, "execute_command", lambda c, q, p=None: c.execute_command(q, p))
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
    monkeypatch.setattr(idx_mod, "execute_query", lambda c, q, p=None: c.execute_query(q, p))
    monkeypatch.setattr(idx_mod, "execute_command", lambda c, q, p=None: c.execute_command(q, p))
    opt = IndexOptimizer(conn)
    stats = opt.analyze_index_usage()
    assert stats and stats[0]["index_name"] == "idx_tbl_col1"
    stmts = opt.recommend_new_indexes("tbl", ["col1", "col2"])
    assert not stmts  # index already exists


def test_apply_recommendations_executes_statements(monkeypatch):
    conn = make_sqlite_conn([])
    monkeypatch.setattr(idx_mod, "execute_query", lambda c, q, p=None: c.execute_query(q, p))
    monkeypatch.setattr(idx_mod, "execute_command", lambda c, q, p=None: c.execute_command(q, p))
    opt = IndexOptimizer(conn)
    opt.apply_recommendations("tbl", ["col1"])
    assert ("CREATE INDEX idx_tbl_col1 ON tbl (col1)", None) in conn.executed
