from yosai_intel_dashboard.src.infrastructure.config.database_manager import MockConnection
from database.intelligent_connection_pool import IntelligentConnectionPool


def factory():
    return MockConnection()


def test_pool_resizes_and_reports_metrics():
    pool = IntelligentConnectionPool(
        factory, min_size=1, max_size=3, timeout=1, shrink_timeout=0
    )

    c1 = pool.get_connection()
    c2 = pool.get_connection()

    # After requesting a second connection utilization should trigger expansion
    assert pool._max_size >= 2

    pool.release_connection(c1)
    pool.release_connection(c2)

    # Shrink happens immediately because shrink_timeout=0
    assert pool._max_size == 1

    metrics = pool.get_metrics()
    assert metrics["acquired"] == 2
    assert metrics["released"] == 2
    assert "avg_acquire_time" in metrics
