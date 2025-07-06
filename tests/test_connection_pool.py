import time

from config.connection_pool import DatabaseConnectionPool
from config.database_manager import MockConnection


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
