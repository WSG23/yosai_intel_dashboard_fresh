import importlib.util
import types
from pathlib import Path
import sys
import pytest

spec = importlib.util.spec_from_file_location(
    "connection_pool",
    Path(__file__).resolve().parents[1]
    / "yosai_intel_dashboard/src/infrastructure/config/connection_pool.py",
)
connection_pool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(connection_pool)
DatabaseConnectionPool = connection_pool.DatabaseConnectionPool

# Stub database_exceptions to avoid heavy imports when loading IntelligentConnectionPool
exc_spec = importlib.util.spec_from_file_location(
    "yosai_intel_dashboard.src.infrastructure.config.database_exceptions",
    Path(__file__).resolve().parents[1]
    / "yosai_intel_dashboard/src/infrastructure/config/database_exceptions.py",
)
db_exc = importlib.util.module_from_spec(exc_spec)
exc_spec.loader.exec_module(db_exc)
sys.modules["yosai_intel_dashboard.src.infrastructure.config.database_exceptions"] = db_exc
config_pkg = types.ModuleType("yosai_intel_dashboard.src.infrastructure.config")
config_pkg.__path__ = []
sys.modules.setdefault(
    "yosai_intel_dashboard.src.infrastructure", types.ModuleType("yosai_intel_dashboard.src.infrastructure")
)
sys.modules["yosai_intel_dashboard.src.infrastructure.config"] = config_pkg

from yosai_intel_dashboard.src.database.intelligent_connection_pool import (
    IntelligentConnectionPool,
)


class MockConnection:
    def __init__(self):
        self._connected = True

    def health_check(self):
        return self._connected

    def close(self):
        self._connected = False


def factory():
    return MockConnection()


def test_database_pool_close_all():
    pool = DatabaseConnectionPool(factory, initial_size=1, max_size=2, timeout=1, shrink_timeout=1)
    active = pool.get_connection()
    idle = pool.get_connection()
    pool.release_connection(idle)
    pool.close_all()
    assert not active._connected
    assert not idle._connected
    with pytest.raises(TimeoutError):
        pool.get_connection()


def test_intelligent_pool_close_all():
    pool = IntelligentConnectionPool(factory, min_size=1, max_size=2, timeout=1, shrink_timeout=1)
    active = pool.get_connection()
    idle = pool.get_connection()
    pool.release_connection(idle)
    pool.close_all()
    assert not active._connected
    assert not idle._connected
    with pytest.raises(TimeoutError):
        pool.get_connection()
