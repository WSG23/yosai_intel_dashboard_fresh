import asyncio
from contextlib import asynccontextmanager

from src.services.database.analytics_service import AnalyticsService


class StubConnection:
    def __init__(self):
        self.queries = []

    def execute_query(self, query):
        self.queries.append(query)
        if "COUNT" in query:
            return [{"count": 1}]
        # recent events
        return [{"event_type": "access", "status": "ok", "timestamp": "now"}]


class StubPool:
    def __init__(self):
        self.health_checks = 0
        self.acquires = 0
        self.releases = 0
        self.connection = StubConnection()

    def health_check(self):
        self.health_checks += 1
        return True

    @asynccontextmanager
    async def acquire_async(self, *, timeout=None):
        self.acquires += 1
        try:
            yield self.connection
        finally:
            self.releases += 1


def test_get_analytics_cache_miss():
    pool = StubPool()
    service = AnalyticsService(pool, ttl=60)
    result = asyncio.run(service.get_analytics())
    assert result["status"] == "success"
    assert pool.health_checks == 1
    assert pool.acquires == 1
    assert pool.releases == 1


def test_get_analytics_cache_hit():
    pool = StubPool()
    service = AnalyticsService(pool, ttl=60)
    first = asyncio.run(service.get_analytics())
    second = asyncio.run(service.get_analytics())
    assert first == second
    assert pool.health_checks == 1
    assert pool.acquires == 1
    assert pool.releases == 1
