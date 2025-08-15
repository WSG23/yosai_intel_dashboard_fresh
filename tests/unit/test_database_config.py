import pytest

from yosai_intel_dashboard.src.infrastructure.config.schema import DatabaseSettings
from yosai_intel_dashboard.src.core.exceptions import ConfigurationError
from yosai_intel_dashboard.src.infrastructure.config.connection_pool import DatabaseConnectionPool
from yosai_intel_dashboard.src.infrastructure.config.database_manager import MockConnection
from yosai_intel_dashboard.src.infrastructure.config.database_exceptions import PoolExhaustedError
from tests.config import FakeConfiguration
from yosai_intel_dashboard.src.core.imports.resolver import safe_import


def factory():
    return MockConnection()


def test_database_config_default_pool_sizes():
    cfg = DatabaseSettings(user="user", password="pass")
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
    with pytest.raises(PoolExhaustedError):
        pool.get_connection()
    for c in conns:
        pool.release_connection(c)


def test_database_settings_requires_credentials():
    with pytest.raises(ConfigurationError):
        DatabaseSettings(user="user", password="", type="postgresql")
