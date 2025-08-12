from threading import Thread
from time import sleep

from yosai_intel_dashboard.src.infrastructure.config.connection_pool import (
    DatabaseConnectionPool,
)
from yosai_intel_dashboard.src.infrastructure.config.connection_retry import RetryConfig
from src.services.database.analytics_service import AnalyticsService


class DummyConnection:
    def execute_query(self, query, params=None):
        if "COUNT" in query:
            return [{"count": 0}]
        return []

    def health_check(self):
        return True

    def close(self):
        pass


def factory():
    return DummyConnection()


def test_retry_acquires_connection_after_release():
    pool = DatabaseConnectionPool(factory, 1, 1, timeout=0.05, shrink_timeout=1)
    retry_cfg = RetryConfig(max_attempts=5, base_delay=0.01, backoff_factor=1.0, jitter=False)
    service = AnalyticsService(
        pool, acquire_timeout=0.05, retry_config=retry_cfg
    )

    def hold_conn():
        with pool.acquire():
            sleep(0.06)

    t = Thread(target=hold_conn)
    t.start()
    result = service.get_analytics()
    t.join()

    assert result["status"] == "success"
    assert "data" in result
