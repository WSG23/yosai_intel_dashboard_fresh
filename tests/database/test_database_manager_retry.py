import dataclasses
import importlib.util
import sys
import types
from pathlib import Path

import pytest
from yosai_intel_dashboard.src.core.imports.resolver import safe_import


def load_database_manager():
    """Import config.database_manager with stubbed dependencies."""
    if "core.unicode" not in sys.modules:
        unicode_mod = types.ModuleType("core.unicode")

        class UnicodeSQLProcessor:
            @staticmethod
            def encode_query(query):
                return str(query)

        unicode_mod.UnicodeSQLProcessor = UnicodeSQLProcessor
        safe_import('core.unicode', unicode_mod)

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
    safe_import('config.schema', schema_mod)

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
    safe_import('config.database_exceptions', ex_mod)

    prot_mod = types.ModuleType("config.protocols")

    class RetryConfigProtocol: ...

    class ConnectionRetryManagerProtocol: ...

    prot_mod.RetryConfigProtocol = RetryConfigProtocol
    prot_mod.ConnectionRetryManagerProtocol = ConnectionRetryManagerProtocol
    safe_import('config.protocols', prot_mod)

    retry_path = Path(__file__).resolve().parents[2] / "config" / "connection_retry.py"
    spec = importlib.util.spec_from_file_location("config.connection_retry", retry_path)
    conn_retry_mod = importlib.util.module_from_spec(spec)
    safe_import('config.connection_retry', conn_retry_mod)
    spec.loader.exec_module(conn_retry_mod)

    dm_path = Path(__file__).resolve().parents[2] / "config" / "database_manager.py"
    spec = importlib.util.spec_from_file_location("config.database_manager", dm_path)
    dbm = importlib.util.module_from_spec(spec)
    safe_import('config.database_manager', dbm)
    spec.loader.exec_module(dbm)
    return dbm


def make_manager(conn, attempts=3):
    dbm = load_database_manager()
    retry_mod = sys.modules["config.connection_retry"]
    cfg = dbm.DatabaseSettings()
    manager = dbm.EnhancedPostgreSQLManager(cfg)
    manager.pool = types.SimpleNamespace(
        get_connection=lambda: conn, release_connection=lambda c: None
    )
    manager.retry_manager = retry_mod.ConnectionRetryManager(
        retry_mod.RetryConfig(max_attempts=attempts, base_delay=0, jitter=False)
    )
    return manager, dbm


class FailingConnection:
    def __init__(self, query_failures=0, health_failures=0):
        self.query_failures = query_failures
        self.health_failures = health_failures
        self.query_calls = 0
        self.health_calls = 0

    def execute_query(self, query, params=None):
        self.query_calls += 1
        if self.query_calls <= self.query_failures:
            raise RuntimeError("boom")
        return [{"ok": True}]

    def execute_command(self, cmd, params=None):
        pass

    def execute_batch(self, cmd, params_seq):
        pass

    def health_check(self):
        self.health_calls += 1
        return self.health_calls > self.health_failures

    def close(self):
        pass


def test_execute_query_retries_until_success():
    conn = FailingConnection(query_failures=2)
    manager, dbm = make_manager(conn, attempts=3)
    result = manager.execute_query_with_retry("SELECT 1")
    assert result == [{"ok": True}]
    assert conn.query_calls == 3


def test_execute_query_retry_exhausted():
    conn = FailingConnection(query_failures=3)
    manager, dbm = make_manager(conn, attempts=2)
    exc = sys.modules["config.database_exceptions"].ConnectionRetryExhausted
    with pytest.raises(exc):
        manager.execute_query_with_retry("SELECT 1")


def test_health_check_retries_until_success():
    conn = FailingConnection(health_failures=1)
    manager, _ = make_manager(conn, attempts=3)
    assert manager.health_check_with_retry() is True
    assert conn.health_calls == 2


def test_health_check_retry_exhausted():
    conn = FailingConnection(health_failures=5)
    manager, dbm = make_manager(conn, attempts=2)
    exc = sys.modules["config.database_exceptions"].ConnectionRetryExhausted
    with pytest.raises(exc):
        manager.health_check_with_retry()
