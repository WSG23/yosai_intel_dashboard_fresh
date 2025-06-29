from config.connection_pool import DatabaseConnectionPool
from config.database_manager import MockConnection
from config.database_exceptions import ConnectionValidationFailed


def factory():
    return MockConnection()


def test_pool_reuse():
    pool = DatabaseConnectionPool(factory, size=2, timeout=10)
    c1 = pool.get_connection()
    pool.release_connection(c1)
    c2 = pool.get_connection()
    assert c1 is c2
    pool.release_connection(c2)


def test_pool_health_check():
    pool = DatabaseConnectionPool(factory, size=1, timeout=10)
    conn = pool.get_connection()
    conn.close()
    pool.release_connection(conn)
    healthy = pool.health_check()
assert not healthy

