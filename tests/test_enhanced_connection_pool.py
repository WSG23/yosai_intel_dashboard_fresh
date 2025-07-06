import pytest

from database.connection_pool import EnhancedConnectionPool, CircuitBreaker
from config.database_manager import MockConnection
from config.database_exceptions import ConnectionValidationFailed


def factory():
    return MockConnection()


def test_pool_metrics():
    pool = EnhancedConnectionPool(factory, 1, 2, timeout=1, shrink_timeout=1)
    conn = pool.get_connection()
    pool.release_connection(conn)
    metrics = pool.get_metrics()
    assert metrics["acquired"] == 1
    assert metrics["released"] == 1
    assert metrics["active"] <= 2


class BadConn:
    def health_check(self):
        return False

    def close(self):
        pass


def bad_factory():
    return BadConn()


def test_circuit_breaker_opens_on_failures():
    pool = EnhancedConnectionPool(
        bad_factory,
        1,
        1,
        timeout=0.1,
        shrink_timeout=0,
        failure_threshold=2,
        recovery_timeout=1,
    )
    with pytest.raises(ConnectionValidationFailed):
        pool.get_connection()
    # second attempt should immediately fail due to open circuit
    with pytest.raises(ConnectionValidationFailed):
        pool.get_connection()
