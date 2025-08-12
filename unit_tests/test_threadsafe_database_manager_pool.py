from __future__ import annotations

from unittest import mock

import pytest
import types
import sys
import os

# Stub core registry to satisfy imports
core_registry = types.ModuleType("yosai_intel_dashboard.src.core.registry")
core_registry.ServiceRegistry = type("ServiceRegistry", (), {})
core_registry.registry = core_registry.ServiceRegistry()
sys.modules.setdefault("yosai_intel_dashboard.src.core.registry", core_registry)

# Minimal pydantic stub for config imports
pydantic_stub = types.ModuleType("pydantic")
class _BaseModel:  # noqa: D401 - simple stub
    """BaseModel stub"""

pydantic_stub.BaseModel = _BaseModel
pydantic_stub.Field = lambda *a, **k: None
pydantic_stub.ValidationError = Exception
pydantic_stub.validator = lambda *a, **k: (lambda f: f)
pydantic_stub.model_validator = pydantic_stub.validator
sys.modules.setdefault("pydantic", pydantic_stub)
os.environ.setdefault("SECRET_KEY", "test")

# Minimal pandas stub
pandas_stub = types.ModuleType("pandas")
pandas_stub.DataFrame = type("DataFrame", (), {})
pandas_stub.Series = type("Series", (), {})
sys.modules.setdefault("pandas", pandas_stub)

# Minimal dash stub
dash_stub = types.ModuleType("dash")
dash_stub.Dash = type("Dash", (), {})
sys.modules.setdefault("dash", dash_stub)
dash_dependencies_stub = types.ModuleType("dash.dependencies")
dash_dependencies_stub.Input = type("Input", (), {})
dash_dependencies_stub.Output = type("Output", (), {})
dash_dependencies_stub.State = type("State", (), {})
sys.modules.setdefault("dash.dependencies", dash_dependencies_stub)
dash_stub.dependencies = dash_dependencies_stub

# Minimal jsonschema stub
jsonschema_stub = types.ModuleType("jsonschema")
jsonschema_stub.ValidationError = Exception
jsonschema_stub.validate = lambda *a, **k: None
sys.modules.setdefault("jsonschema", jsonschema_stub)

# Additional stubs for database_manager dependencies
text_utils_stub = types.ModuleType("yosai_intel_dashboard.src.utils.text_utils")
text_utils_stub.safe_text = lambda s: s
sys.modules.setdefault("yosai_intel_dashboard.src.utils.text_utils", text_utils_stub)

core_unicode_stub = types.ModuleType("yosai_intel_dashboard.src.core.unicode")
core_unicode_stub.UnicodeSQLProcessor = types.SimpleNamespace(encode_query=lambda q: q)
sys.modules.setdefault("yosai_intel_dashboard.src.core.unicode", core_unicode_stub)

query_opt_stub = types.ModuleType("yosai_intel_dashboard.src.database.query_optimizer")
query_opt_stub.DatabaseQueryOptimizer = type("DatabaseQueryOptimizer", (), {})
sys.modules.setdefault(
    "yosai_intel_dashboard.src.database.query_optimizer", query_opt_stub
)

repl_conn_stub = types.ModuleType("yosai_intel_dashboard.src.database.replicated_connection")
repl_conn_stub.ReplicatedDatabaseConnection = type(
    "ReplicatedDatabaseConnection", (), {}
)
sys.modules.setdefault(
    "yosai_intel_dashboard.src.database.replicated_connection", repl_conn_stub
)

secure_exec_stub = types.ModuleType("yosai_intel_dashboard.src.database.secure_exec")
secure_exec_stub.execute_batch = lambda *a, **k: None
secure_exec_stub.execute_command = lambda *a, **k: None
secure_exec_stub.execute_query = lambda *a, **k: []
sys.modules.setdefault(
    "yosai_intel_dashboard.src.database.secure_exec", secure_exec_stub
)

db_types_stub = types.ModuleType("yosai_intel_dashboard.src.database.types")
class _DBConnection:
    pass

db_types_stub.DatabaseConnection = _DBConnection
db_types_stub.DBRows = list
sys.modules.setdefault("yosai_intel_dashboard.src.database.types", db_types_stub)

db_exc_stub = types.ModuleType(
    "yosai_intel_dashboard.src.infrastructure.config.database_exceptions"
)
db_exc_stub.ConnectionValidationFailed = type(
    "ConnectionValidationFailed", (Exception,), {}
)
db_exc_stub.DatabaseError = type("DatabaseError", (Exception,), {})
sys.modules.setdefault(
    "yosai_intel_dashboard.src.infrastructure.config.database_exceptions",
    db_exc_stub,
)

protocols_stub = types.ModuleType(
    "yosai_intel_dashboard.src.infrastructure.config.protocols"
)
protocols_stub.ConnectionRetryManagerProtocol = object
protocols_stub.RetryConfigProtocol = object
sys.modules.setdefault(
    "yosai_intel_dashboard.src.infrastructure.config.protocols", protocols_stub
)

schema_stub = types.ModuleType(
    "yosai_intel_dashboard.src.infrastructure.config.schema"
)
schema_stub.DatabaseSettings = type("DatabaseSettings", (), {})
sys.modules.setdefault(
    "yosai_intel_dashboard.src.infrastructure.config.schema", schema_stub
)

import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "yosai_intel_dashboard.src.infrastructure.config.database_manager",
    Path(__file__).resolve().parents[1]
    / "yosai_intel_dashboard"
    / "src"
    / "infrastructure"
    / "config"
    / "database_manager.py",
)
database_manager = importlib.util.module_from_spec(spec)
spec.loader.exec_module(database_manager)  # type: ignore
ThreadSafeDatabaseManager = database_manager.ThreadSafeDatabaseManager


@pytest.fixture
def mock_pool_success(mock_db_connection):
    pool = mock.Mock()
    pool.get_connection.return_value = mock_db_connection
    return pool


@pytest.fixture
def mock_pool_timeout():
    pool = mock.Mock()
    pool.get_connection.side_effect = TimeoutError("No available connection")
    return pool


def test_manager_releases_connection_and_invalidates_cache(
    monkeypatch, mock_pool_success, mock_db_connection
):
    settings = types.SimpleNamespace(type="mock")
    manager = ThreadSafeDatabaseManager(settings)
    monkeypatch.setattr(manager, "_create_pool", lambda: mock_pool_success)

    conn = manager.get_connection()
    assert conn is mock_db_connection
    assert manager._pool is mock_pool_success

    manager.release_connection(conn)
    mock_pool_success.release_connection.assert_called_once_with(mock_db_connection)

    manager.close()
    mock_pool_success.close_all.assert_called_once()
    assert manager._pool is None


def test_manager_get_connection_timeout(monkeypatch, mock_pool_timeout):
    settings = types.SimpleNamespace(type="mock")
    manager = ThreadSafeDatabaseManager(settings)
    monkeypatch.setattr(manager, "_create_pool", lambda: mock_pool_timeout)

    with pytest.raises(TimeoutError):
        manager.get_connection()
    assert manager._pool is mock_pool_timeout
    mock_pool_timeout.release_connection.assert_not_called()

    manager.close()
    mock_pool_timeout.close_all.assert_called_once()
    assert manager._pool is None
