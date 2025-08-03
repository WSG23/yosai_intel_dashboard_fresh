import threading
import importlib.util
from pathlib import Path

spec_cp = importlib.util.spec_from_file_location(
    "connection_pool",
    Path(__file__).resolve().parents[1]
    / "yosai_intel_dashboard"
    / "src"
    / "infrastructure"
    / "config"
    / "connection_pool.py",
)
cp_module = importlib.util.module_from_spec(spec_cp)
spec_cp.loader.exec_module(cp_module)  # type: ignore
DatabaseConnectionPool = cp_module.DatabaseConnectionPool



class MockConnection:
    def __init__(self):
        self._connected = True

    def execute_query(self, query, params=None):
        return []

    def execute_command(self, command, params=None):
        return None


    def health_check(self):
        return self._connected

    def close(self):
        self._connected = False


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
