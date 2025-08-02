import pytest

from yosai_intel_dashboard.src.services.migration.validators.integrity_checker import IntegrityChecker
from yosai_intel_dashboard.src.services.optimized_queries import OptimizedQueryService


class RecordingConn:
    def __init__(self):
        self.last_query = None
        self.last_params = None

    def execute_query(self, query, params=None):
        self.last_query = query
        self.last_params = params
        return []


class RecordingPool:
    def __init__(self):
        self.last_query = None

    async def fetchval(self, query, *params):
        self.last_query = query
        return 0


def test_batch_get_users_injection():
    conn = RecordingConn()
    service = OptimizedQueryService(conn)
    malicious = "1; DROP TABLE people;"
    service.batch_get_users([malicious])
    assert malicious in conn.last_params[0]
    assert malicious not in conn.last_query


@pytest.mark.asyncio
async def test_rowcount_equal_injection():
    pool = RecordingPool()
    checker = IntegrityChecker()
    malicious = "danger; DROP TABLE x;"
    await checker.rowcount_equal(pool, pool, malicious)
    assert malicious in pool.last_query
    assert pool.last_query.startswith('SELECT COUNT(*) FROM "')
