import asyncio

from yosai_intel_dashboard.src.infrastructure.config.connection_pool import (
    DatabaseConnectionPool,
)
from src.services.database.analytics_service import AnalyticsService


class DummyConnection:
    def execute_query(self, query, params=None):
        return []

    def health_check(self):
        return True

    def close(self):
        pass


def factory():
    return DummyConnection()


def test_pool_exhaustion_returns_error():
    pool = DatabaseConnectionPool(factory, 1, 1, timeout=0.1, shrink_timeout=1)
    service = AnalyticsService(pool, acquire_timeout=0.1)

    with pool.acquire():
        result = asyncio.run(service.get_analytics())

    assert result["status"] == "error"
    assert result["error_code"] == "pool_timeout"
