from __future__ import annotations

import importlib.util
import threading
import time
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "connection_pool",
    Path(__file__).resolve().parents[1]
    / "yosai_intel_dashboard/src/infrastructure/config/connection_pool.py",
)
connection_pool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(connection_pool)  # type: ignore[attr-defined]
DatabaseConnectionPool = connection_pool.DatabaseConnectionPool


class MockConnection:
    def __init__(self) -> None:
        self.closed = False

    def health_check(self) -> bool:
        return not self.closed

    def close(self) -> None:
        self.closed = True



def factory():
    return MockConnection()


def test_pool_thread_safety():
    pool = DatabaseConnectionPool(
        factory, initial_size=1, max_size=3, timeout=10, shrink_timeout=10
    )
    results = []
    max_active = []
    lock = threading.Lock()

    def worker():
        conn = pool.get_connection()
        with lock:
            max_active.append(pool._active)
        time.sleep(0.05)
        results.append(conn)
        pool.release_connection(conn)

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(results) == 10
    assert max(max_active) <= pool._max_pool_size


def test_pool_blocks_until_connection_available():
    pool = DatabaseConnectionPool(
        factory, initial_size=1, max_size=1, timeout=5, shrink_timeout=10
    )

    def worker():
        conn = pool.get_connection()
        time.sleep(0.1)
        pool.release_connection(conn)

    threads = [threading.Thread(target=worker) for _ in range(3)]
    start = time.time()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    duration = time.time() - start

    # With only one connection available, the total duration should reflect
    # sequential access by each thread.
    assert duration >= 0.25
