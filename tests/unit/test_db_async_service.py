import asyncio
from contextlib import asynccontextmanager

from src.services.database.analytics_service import AnalyticsService


class Conn:
    def execute_query(self, query):
        if "COUNT" in query:
            return [{"count": 1}]
        return [{"event_type": "login", "status": "success", "timestamp": "2024-01-01"}]


class Pool:
    def health_check(self):
        return True

    @asynccontextmanager
    async def acquire_async(self, *, timeout=None):
        yield Conn()


def test_get_analytics_async():
    service = AnalyticsService(Pool())
    result = asyncio.run(service.get_analytics())
    assert result["status"] == "success"
    assert result["data"]["user_count"] == 1
