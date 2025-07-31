import threading

from yosai_intel_dashboard.src.infrastructure.config.connection_pool import DatabaseConnectionPool
from yosai_intel_dashboard.src.infrastructure.config.database_manager import MockConnection


def factory():
    return MockConnection()


def test_pool_thread_safety():
    pool = DatabaseConnectionPool(
        factory, initial_size=1, max_size=3, timeout=10, shrink_timeout=10
    )
    results = []

    def worker():
        conn = pool.get_connection()
        results.append(conn)
        pool.release_connection(conn)

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(results) == 10
    assert pool._active <= pool._max_pool_size
