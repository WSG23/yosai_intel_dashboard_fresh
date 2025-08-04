import dataclasses
import importlib.util
import sys
import types
from pathlib import Path
from yosai_intel_dashboard.src.core.imports.resolver import safe_import


def stub_config_and_core():
    pkg = types.ModuleType("config")
    pkg.__path__ = []
    safe_import('config', pkg)
    safe_import('config.dynamic_config', types.ModuleType("config.dynamic_config"))
    sys.modules["config.dynamic_config"].dynamic_config = types.SimpleNamespace(
        get_db_connection_timeout=lambda: 1,
        get_db_pool_size=lambda: 1,
    )

    @dataclasses.dataclass
    class DatabaseSettings:
        type: str = "mock"
        host: str = "localhost"
        port: int = 0
        name: str = "db"
        user: str = "user"
        password: str = ""
        connection_timeout: int = 1

    pkg.DatabaseSettings = DatabaseSettings

    cache_mod = types.ModuleType("core.cache_manager")

    class InMemoryCacheManager:
        def __init__(self, config=None):
            self.store = {}

        async def start(self):
            pass

        async def stop(self):
            self.store.clear()

        async def get(self, key):
            return self.store.get(key)

        async def set(self, key, value, ttl=None):
            self.store[key] = value

        async def delete(self, key):
            return self.store.pop(key, None) is not None

        async def clear(self):
            self.store.clear()

        def get_lock(self, key, timeout=10):
            class _Lock:
                async def __aenter__(self):
                    pass

                async def __aexit__(self, exc_type, exc, tb):
                    pass

            return _Lock()

    class CacheConfig:
        pass

    def cache_with_lock(manager, ttl=None, key_func=None, name=None):
        def decorator(func):
            cache = {}

            def wrapper(*args, **kwargs):
                key = key_func(*args, **kwargs) if key_func else "k"
                if key in cache:
                    return cache[key]
                result = func(*args, **kwargs)
                cache[key] = result
                return result

            return wrapper

        return decorator

    cache_mod.InMemoryCacheManager = InMemoryCacheManager
    cache_mod.CacheConfig = CacheConfig
    cache_mod.cache_with_lock = cache_with_lock
    safe_import('core.cache_manager', cache_mod)


stub_config_and_core()

from yosai_intel_dashboard.src.services.database_retriever import DatabaseAnalyticsRetriever
from yosai_intel_dashboard.src.services.db_analytics_helper import DatabaseAnalyticsHelper

module_path = (
    Path(__file__).resolve().parents[2] / "services" / "database_analytics_service.py"
)
spec = importlib.util.spec_from_file_location(
    "services.database_analytics_service", module_path
)
db_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(db_module)
DatabaseAnalyticsService = db_module.DatabaseAnalyticsService


class ErrorManager:
    def get_connection(self):
        raise RuntimeError("fail")

    def release_connection(self, conn):
        pass


class BadQueryConnection:
    def execute_query(self, query, params=None):
        raise RuntimeError("bad query")

    def execute_command(self, cmd, params=None):
        pass

    def execute_batch(self, cmd, params_seq):
        pass

    def health_check(self):
        return True

    def close(self):
        pass


class SimpleManager:
    def __init__(self, conn):
        self._conn = conn

    def get_connection(self):
        return self._conn

    def release_connection(self, conn):
        pass


def test_service_returns_error_when_connection_fails():
    service = DatabaseAnalyticsService(ErrorManager())
    result = service.get_analytics()
    assert result["status"] == "error"


def test_service_returns_error_on_query_failure():
    service = DatabaseAnalyticsService(SimpleManager(BadQueryConnection()))
    result = service.get_analytics()
    assert result["status"] == "error"


def test_retriever_caches_results():
    class Helper(DatabaseAnalyticsHelper):
        def __init__(self):
            self.calls = 0

        def get_analytics(self):
            self.calls += 1
            return {"value": self.calls}

    helper = Helper()
    retriever = DatabaseAnalyticsRetriever(helper)
    first = retriever.get_analytics()
    second = retriever.get_analytics()
    assert first == second
    assert helper.calls == 1


def test_service_success_with_sqlite(tmp_path):
    db_file = tmp_path / "test.db"

    @dataclasses.dataclass
    class DS:
        type: str = "sqlite"
        host: str = "localhost"
        port: int = 0
        name: str = str(db_file)
        user: str = ""
        password: str = ""
        connection_timeout: int = 1
        initial_pool_size: int = 1
        max_pool_size: int = 1
        shrink_timeout: int = 0

    dm_path = Path(__file__).resolve().parents[2] / "config" / "database_manager.py"
    spec = importlib.util.spec_from_file_location("config.database_manager", dm_path)
    dm_mod = importlib.util.module_from_spec(spec)
    safe_import('config.database_manager', dm_mod)
    spec.loader.exec_module(dm_mod)
    conn = dm_mod.SQLiteConnection(DS())
    conn.execute_command(
        "CREATE TABLE access_events(event_type TEXT, status TEXT, timestamp TEXT, location TEXT)"
    )
    conn.execute_command(
        'INSERT INTO access_events(event_type, status, timestamp, location) VALUES("access","success","2021-01-01","A")'
    )

    class Manager(SimpleManager):
        pass

    manager = Manager(conn)
    service = DatabaseAnalyticsService(manager)
    result = service.get_analytics()
    assert result["status"] == "success"
    conn.close()
