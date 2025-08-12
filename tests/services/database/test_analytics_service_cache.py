import asyncio
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


class StubManager:
    def __init__(self):
        self.health_checks = 0
        self.gets = 0
        self.releases = 0
        self.connection = StubConnection()

    def health_check(self):
        self.health_checks += 1
        return True

    def get_connection(self):
        self.gets += 1
        return self.connection

    def release_connection(self, conn):
        self.releases += 1


def test_aget_analytics_cache_miss():
    manager = StubManager()
    service = AnalyticsService(manager, ttl=60)
    result = asyncio.run(service.aget_analytics())
    assert result["status"] == "success"
    assert manager.health_checks == 1
    assert manager.gets == 1
    assert manager.releases == 1


def test_get_analytics_cache_hit():
    manager = StubManager()
    service = AnalyticsService(manager, ttl=60)
    first = service.get_analytics()
    second = service.get_analytics()
    assert first == second
    assert manager.health_checks == 1
    assert manager.gets == 1
    assert manager.releases == 1
