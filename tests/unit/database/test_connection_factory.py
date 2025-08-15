import time
import types
import sys
import dataclasses
from types import SimpleNamespace
from pathlib import Path
import importlib.util

import pytest
import asyncpg

from yosai_intel_dashboard.src.core.imports.resolver import safe_import


def load_dbm_modules():
    if "yosai_intel_dashboard.src.core.unicode" not in sys.modules:
        unicode_mod = types.ModuleType("yosai_intel_dashboard.src.core.unicode")

        class UnicodeSQLProcessor:
            @staticmethod
            def encode_query(query):
                return str(query)

        unicode_mod.UnicodeSQLProcessor = UnicodeSQLProcessor
        core_pkg = types.ModuleType("yosai_intel_dashboard.src.core")
        core_pkg.__path__ = []
        core_pkg.unicode = unicode_mod
        src_pkg = types.ModuleType("yosai_intel_dashboard.src")
        src_pkg.__path__ = []
        src_pkg.core = core_pkg
        root_pkg = types.ModuleType("yosai_intel_dashboard")
        root_pkg.__path__ = []
        root_pkg.src = src_pkg
        sys.modules.setdefault("yosai_intel_dashboard", root_pkg)
        sys.modules.setdefault("yosai_intel_dashboard.src", src_pkg)
        sys.modules.setdefault("yosai_intel_dashboard.src.core", core_pkg)
        sys.modules["yosai_intel_dashboard.src.core.unicode"] = unicode_mod

    pkg = types.ModuleType("config")
    pkg.__path__ = []
    sys.modules["config"] = pkg

    sys.modules["config.dynamic_config"] = types.ModuleType("config.dynamic_config")
    sys.modules["config.dynamic_config"].dynamic_config = types.SimpleNamespace(
        get_db_connection_timeout=lambda: 1,
        get_db_pool_size=lambda: 1,
    )

    @dataclasses.dataclass
    class DatabaseSettings:
        type: str = "mock"
        host: str = "localhost"
        port: int = 5432
        name: str = "db"
        user: str = "user"
        password: str = ""
        connection_timeout: int = 1
        initial_pool_size: int = 1
        max_pool_size: int = 1
        shrink_timeout: int = 0

    schema_mod = types.ModuleType("config.schema")
    schema_mod.DatabaseSettings = DatabaseSettings
    sys.modules["config.schema"] = schema_mod

    ex_mod = types.ModuleType("config.database_exceptions")

    class ConnectionRetryExhausted(Exception):
        pass

    class ConnectionValidationFailed(Exception):
        pass

    class DatabaseError(Exception):
        pass

    ex_mod.ConnectionRetryExhausted = ConnectionRetryExhausted
    ex_mod.ConnectionValidationFailed = ConnectionValidationFailed
    ex_mod.DatabaseError = DatabaseError
    sys.modules["config.database_exceptions"] = ex_mod

    prot_mod = types.ModuleType("config.protocols")

    class RetryConfigProtocol: ...

    class ConnectionRetryManagerProtocol: ...

    prot_mod.RetryConfigProtocol = RetryConfigProtocol
    prot_mod.ConnectionRetryManagerProtocol = ConnectionRetryManagerProtocol
    sys.modules["config.protocols"] = prot_mod

    if "database" not in sys.modules:
        db_pkg = types.ModuleType("database")
        db_pkg.query_optimizer = types.ModuleType("database.query_optimizer")
        
        class DatabaseQueryOptimizer:
            def optimize_query(self, query):
                return query
        
        db_pkg.query_optimizer.DatabaseQueryOptimizer = DatabaseQueryOptimizer
        db_pkg.secure_exec = types.ModuleType("database.secure_exec")
        db_pkg.secure_exec.execute_query = (
            lambda conn, q, params=None: conn.execute_query(q, params)
        )
        db_pkg.secure_exec.execute_command = (
            lambda conn, cmd, params=None: conn.execute_command(cmd, params)
        )
        db_pkg.secure_exec.execute_batch = (
            lambda conn, cmd, params_seq: (
                conn.execute_batch(cmd, params_seq)
                if hasattr(conn, "execute_batch")
                else conn.executemany(cmd, params_seq)
            )
        )
        db_pkg.types = types.ModuleType("database.types")
        class DatabaseConnection: ...
        db_pkg.types.DatabaseConnection = DatabaseConnection
        db_pkg.intelligent_connection_pool = types.ModuleType(
            "database.intelligent_connection_pool"
        )
        class IntelligentConnectionPool:
            def __init__(self, *a, **k):
                pass
            def get_connection(self):
                raise RuntimeError
            def release_connection(self, conn):
                pass
        db_pkg.intelligent_connection_pool.IntelligentConnectionPool = (
            IntelligentConnectionPool
        )
        db_pkg.performance_analyzer = types.ModuleType(
            "database.performance_analyzer"
        )
        class DatabasePerformanceAnalyzer:
            def analyze_query_performance(self, *a, **k):
                pass
        db_pkg.performance_analyzer.DatabasePerformanceAnalyzer = (
            DatabasePerformanceAnalyzer
        )
        sys.modules["database"] = db_pkg
        sys.modules["database.query_optimizer"] = db_pkg.query_optimizer
        sys.modules["database.secure_exec"] = db_pkg.secure_exec
        sys.modules["database.types"] = db_pkg.types
        sys.modules["database.intelligent_connection_pool"] = (
            db_pkg.intelligent_connection_pool
        )
        sys.modules["database.performance_analyzer"] = db_pkg.performance_analyzer

    root = Path(__file__).resolve().parents[2]
    retry_path = root / "config" / "connection_retry.py"
    spec = importlib.util.spec_from_file_location("config.connection_retry", retry_path)
    retry_mod = importlib.util.module_from_spec(spec)
    sys.modules["config.connection_retry"] = retry_mod
    spec.loader.exec_module(retry_mod)

    dm_path = root / "config" / "database_manager.py"
    spec = importlib.util.spec_from_file_location("config.database_manager", dm_path)
    dbm_mod = importlib.util.module_from_spec(spec)
    sys.modules["config.database_manager"] = dbm_mod
    spec.loader.exec_module(dbm_mod)

    return dbm_mod, retry_mod, DatabaseSettings


def load_async_manager():
    """Load AsyncPostgreSQLManager without triggering heavy imports."""
    const_mod = types.ModuleType(
        "yosai_intel_dashboard.src.infrastructure.config.constants"
    )
    const_mod.DEFAULT_DB_HOST = "localhost"
    const_mod.DEFAULT_DB_PORT = 5432
    sys.modules[
        "yosai_intel_dashboard.src.infrastructure.config.constants"
    ] = const_mod

    prof_mod = types.ModuleType("monitoring.performance_profiler")

    class PerformanceProfiler:  # pragma: no cover - simple stub
        def track_db_query(self, query):
            class Ctx:
                async def __aenter__(self):
                    return None

                async def __aexit__(self, exc_type, exc, tb):
                    return False

            return Ctx()

    prof_mod.PerformanceProfiler = PerformanceProfiler
    sys.modules["monitoring.performance_profiler"] = prof_mod

    path = (
        Path(__file__).resolve().parents[2]
        / "yosai_intel_dashboard"
        / "src"
        / "core"
        / "plugins"
        / "config"
        / "async_database_manager.py"
    )
    spec = importlib.util.spec_from_file_location(
        "async_database_manager", path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.AsyncPostgreSQLManager


_dbm, _retry, DatabaseSettings = load_dbm_modules()
ConnectionRetryManager = _retry.ConnectionRetryManager
RetryConfig = _retry.RetryConfig
DatabaseManager = _dbm.DatabaseManager
EnhancedPostgreSQLManager = _dbm.EnhancedPostgreSQLManager
AsyncPostgreSQLManager = load_async_manager()


class DummyProfiler:
    """Minimal profiler context manager for async operations."""

    class _Ctx:
        async def __aenter__(self):
            return None

        async def __aexit__(self, exc_type, exc, tb):
            return False

    def track_db_query(self, query: str):
        return self._Ctx()


@pytest.mark.asyncio
async def test_pool_sizing_and_auto_return(monkeypatch):
    """Ensure async pool respects size and connections are returned."""

    creation_args = {}

    class FakePool:
        def __init__(self):
            self.acquired = 0
            self.released = 0

        def acquire(self):
            pool = self

            class _Ctx:
                async def __aenter__(self):
                    pool.acquired += 1

                    class Conn:
                        async def fetch(self, query, *params):
                            return ["ok"]

                    self.conn = Conn()
                    return self.conn

                async def __aexit__(self, exc_type, exc, tb):
                    pool.released += 1

            return _Ctx()

        async def close(self):
            pass

    async def fake_create_pool(*args, **kwargs):
        creation_args["kwargs"] = kwargs
        return FakePool()

    monkeypatch.setattr(asyncpg, "create_pool", fake_create_pool)

    cfg = SimpleNamespace(
        host="h",
        port=1,
        name="n",
        user="u",
        password="p",
        initial_pool_size=1,
        max_pool_size=4,
        connection_timeout=3,
    )

    manager = AsyncPostgreSQLManager(cfg)
    manager._profiler = DummyProfiler()

    result = await manager.execute("SELECT 1")
    assert result == ["ok"]
    assert creation_args["kwargs"]["min_size"] == 1
    assert creation_args["kwargs"]["max_size"] == 4
    assert manager.pool.acquired == 1
    assert manager.pool.released == 1


@pytest.mark.asyncio
async def test_async_interface_health_check(monkeypatch):
    """Async manager should run health checks using asyncpg pool."""

    class FakePool:
        def __init__(self):
            self.acquired = 0
            self.released = 0

        def acquire(self):
            pool = self

            class _Ctx:
                async def __aenter__(self):
                    pool.acquired += 1

                    class Conn:
                        async def execute(self, query):
                            return None

                    self.conn = Conn()
                    return self.conn

                async def __aexit__(self, exc_type, exc, tb):
                    pool.released += 1

            return _Ctx()

        async def close(self):
            pass

    async def fake_create_pool(*args, **kwargs):
        return FakePool()

    monkeypatch.setattr(asyncpg, "create_pool", fake_create_pool)

    cfg = SimpleNamespace(
        host="h",
        port=1,
        name="n",
        user="u",
        password="p",
        initial_pool_size=1,
        max_pool_size=2,
        connection_timeout=3,
    )

    manager = AsyncPostgreSQLManager(cfg)
    manager._profiler = DummyProfiler()

    ok = await manager.health_check()
    assert ok is True
    assert manager.pool.acquired == 1
    assert manager.pool.released == 1


def _make_enhanced_manager():
    settings = DatabaseSettings(
        type="postgresql",
        initial_pool_size=0,
        max_pool_size=1,
        connection_timeout=1,
        shrink_timeout=0,
    )
    manager = EnhancedPostgreSQLManager(settings)
    manager.optimizer.optimize_query = lambda q: q
    return manager


def test_retry_with_exponential_backoff(monkeypatch):
    manager = _make_enhanced_manager()

    class FlakyConn:
        def __init__(self):
            self.calls = 0

        def execute_query(self, query, params=None):
            self.calls += 1
            if self.calls < 3:
                raise RuntimeError("boom")
            return "ok"

        def health_check(self):
            return True

        def close(self):
            pass

        def execute_batch(self, command, params_seq):
             pass

    conn = FlakyConn()

    class Pool:
        def __init__(self):
            self.releases = 0

        def get_connection(self):
            return conn

        def release_connection(self, _):
            self.releases += 1

    manager.pool = Pool()
    cfg = RetryConfig(max_attempts=3, base_delay=0.1, backoff_factor=2, jitter=False)
    manager.retry_manager = ConnectionRetryManager(cfg)

    sleeps = []
    monkeypatch.setattr(time, "sleep", lambda d: sleeps.append(d))
    monkeypatch.setattr(
        "yosai_intel_dashboard.src.core.unicode.UnicodeSQLProcessor.encode_query",
        lambda q: q,
    )

    result = manager.execute_query_with_retry("SELECT 1")
    assert result == "ok"
    assert conn.calls == 3
    assert manager.pool.releases == 3
    assert sleeps == [0.1, 0.2]


def test_unicode_query_parameter_handling(monkeypatch):
    manager = _make_enhanced_manager()

    class Conn:
        def __init__(self):
            self.query = None
            self.params = None

        def execute_query(self, query, params=None):
            self.query = query
            self.params = params
            return "done"

        def health_check(self):
            return True

        def close(self):
            pass

        def execute_batch(self, command, params_seq):
            pass

    conn = Conn()

    class Pool:
        def get_connection(self):
            return conn

        def release_connection(self, _):
            pass

    manager.pool = Pool()
    manager.retry_manager = ConnectionRetryManager(
        RetryConfig(max_attempts=1, base_delay=0, jitter=False)
    )
    monkeypatch.setattr(
        "yosai_intel_dashboard.src.core.unicode.UnicodeSQLProcessor.encode_query",
        lambda q: f"ENC:{q}",
    )

    manager.execute_query_with_retry("SELECT '漢字'", params=("漢字",))
    assert conn.query == "ENC:SELECT '漢字'"
    assert conn.params == ("ENC:漢字",)


@pytest.mark.parametrize("db_type", ["postgresql", "sqlite", "mock"])
def test_health_check_backends(monkeypatch, db_type):
    settings = DatabaseSettings(type=db_type)
    manager = DatabaseManager(settings)

    conn = SimpleNamespace(health_check=lambda: True, close=lambda: None)
    monkeypatch.setattr(manager, "_create_connection", lambda: conn)

    assert manager.health_check() is True
