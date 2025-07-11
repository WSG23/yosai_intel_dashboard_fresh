import pytest

from config import DatabaseConfig
from tests.fake_configuration import FakeConfiguration
from config.connection_pool import DatabaseConnectionPool
from config.database_manager import MockConnection


def factory():
    return MockConnection()


def test_database_config_default_pool_sizes():
    cfg = DatabaseConfig()
    fake_cfg = FakeConfiguration()
    assert cfg.initial_pool_size == fake_cfg.get_db_pool_size()
    assert cfg.max_pool_size == cfg.initial_pool_size * 2

    pool = DatabaseConnectionPool(
        factory,
        initial_size=cfg.initial_pool_size,
        max_size=cfg.max_pool_size,
        timeout=1,
        shrink_timeout=0,
    )

    conns = [pool.get_connection() for _ in range(cfg.max_pool_size)]
    with pytest.raises(TimeoutError):
        pool.get_connection()
    for c in conns:
        pool.release_connection(c)
