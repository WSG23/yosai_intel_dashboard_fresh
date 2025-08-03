import time

import importlib.util
from pathlib import Path

# Import connection_pool without triggering heavy package imports
spec = importlib.util.spec_from_file_location(
    "connection_pool",
    Path(__file__).resolve().parents[1]
    / "yosai_intel_dashboard/src/infrastructure/config/connection_pool.py",
)
connection_pool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(connection_pool)
DatabaseConnectionPool = connection_pool.DatabaseConnectionPool


class MockConnection:
    def __init__(self):
        self._connected = True

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
