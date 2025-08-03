import time
import importlib.util
from pathlib import Path

spec_cp = importlib.util.spec_from_file_location(
    "yosai_intel_dashboard.src.infrastructure.config.connection_pool",
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

    def execute_batch(self, command, params_seq):
        return None

    def health_check(self):
        return self._connected

    def close(self):
        self._connected = False


def factory():
    return MockConnection()


def test_pool_reuse():
    pool = DatabaseConnectionPool(
        factory, initial_size=2, max_size=4, timeout=10, shrink_timeout=1
    )
    c1 = pool.get_connection()
    pool.release_connection(c1)
    c2 = pool.get_connection()
    assert c1 is c2
    pool.release_connection(c2)


def test_pool_health_check():
    pool = DatabaseConnectionPool(
        factory, initial_size=1, max_size=2, timeout=10, shrink_timeout=1
    )
    conn = pool.get_connection()
    conn.close()
    pool.release_connection(conn)
    healthy = pool.health_check()
    assert healthy


def test_pool_expands_and_shrinks():
    pool = DatabaseConnectionPool(
        factory, initial_size=1, max_size=3, timeout=10, shrink_timeout=0
    )

    c1 = pool.get_connection()
    # First connection should not trigger expansion
    assert pool._max_size == 1

    c2 = pool.get_connection()
    # Requesting a second concurrent connection should expand the pool
    assert pool._max_size >= 2

    pool.release_connection(c1)
    pool.release_connection(c2)

    # Shrink happens immediately due to shrink_timeout=0
    assert pool._max_size == 1


def test_periodic_shrink_closes_idle_connections():
    pool = DatabaseConnectionPool(
        factory,
        initial_size=1,
        max_size=3,
        timeout=1,
        shrink_timeout=1,
        idle_timeout=0.05,
        shrink_interval=0.05,
    )

    c1 = pool.get_connection()
    c2 = pool.get_connection()
    pool.release_connection(c1)
    pool.release_connection(c2)
    assert pool._max_size == 2

    time.sleep(0.2)

    assert pool._max_size == 1
    closed = sum(not c._connected for c in (c1, c2))
    assert closed == 1


def test_warmup_prefills_pool():
    class WarmConn:
        def __init__(self):
            self.warm_calls = 0
            self._connected = True

        def execute_query(self, query, params=None):
            self.warm_calls += 1
            return []

        def execute_command(self, command, params=None):
            return None

        def health_check(self):
            return True

        def close(self):
            self._connected = False

    def warm_factory():
        return WarmConn()

    pool = DatabaseConnectionPool(warm_factory, 1, 2, timeout=1, shrink_timeout=1)
    conn, _ = pool._pool[0]
    assert conn.warm_calls == 1

    conn.close()
    pool._pool.clear()
    pool._active = 0

    pool.warmup()
    assert pool._active == 1
    conn, _ = pool._pool[0]
    assert conn.warm_calls == 1
