import pytest
import threading
import time

from database.intelligent_connection_pool import (
    IntelligentConnectionPool,
    CircuitBreaker,
)
from config.database_manager import MockConnection
from config.database_exceptions import ConnectionValidationFailed


def factory():
    return MockConnection()


def test_pool_metrics():
    pool = IntelligentConnectionPool(factory, 1, 2, timeout=1, shrink_timeout=1)
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
    pool = IntelligentConnectionPool(
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


def test_connection_count_under_load():
    pool = IntelligentConnectionPool(factory, 2, 4, timeout=1, shrink_timeout=1)
    results = []
    lock = threading.Lock()

    def worker():
        conn = pool.get_connection()
        with lock:
            results.append(conn)
        time.sleep(0.01)
        pool.release_connection(conn)

    threads = [threading.Thread(target=worker) for _ in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(set(results)) <= pool._max_pool_size
    metrics = pool.get_metrics()
    assert metrics["acquired"] == 20
    assert metrics["released"] == 20
