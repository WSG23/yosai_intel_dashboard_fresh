from __future__ import annotations

import sys
import types
from unittest.mock import MagicMock

import pytest

# Stub core package hierarchy
core_pkg = types.ModuleType("yosai_intel_dashboard.src.core")
core_pkg.__path__ = []  # type: ignore[attr-defined]
sys.modules["yosai_intel_dashboard.src.core"] = core_pkg

interfaces_pkg = types.ModuleType("yosai_intel_dashboard.src.core.interfaces")
interfaces_pkg.__path__ = []  # type: ignore[attr-defined]
sys.modules["yosai_intel_dashboard.src.core.interfaces"] = interfaces_pkg

protocols_mod = types.ModuleType("yosai_intel_dashboard.src.core.interfaces.protocols")
protocols_mod.DatabaseProtocol = type("DatabaseProtocol", (), {})
sys.modules["yosai_intel_dashboard.src.core.interfaces.protocols"] = protocols_mod

core_audit = types.ModuleType("yosai_intel_dashboard.src.core.audit_logger")


class ComplianceAuditLogger:  # pragma: no cover - simple stub
    def log_action(self, *args, **kwargs):
        pass


core_audit.ComplianceAuditLogger = ComplianceAuditLogger
sys.modules["yosai_intel_dashboard.src.core.audit_logger"] = core_audit

core_unicode = types.ModuleType("yosai_intel_dashboard.src.core.unicode")
core_unicode.safe_unicode_encode = lambda v: v
sys.modules["yosai_intel_dashboard.src.core.unicode"] = core_unicode

# Stub database.secure_exec
database_pkg = types.ModuleType("database")
database_pkg.__path__ = []  # type: ignore[attr-defined]
sys.modules["database"] = database_pkg
secure_exec_mod = types.ModuleType("database.secure_exec")


def execute_command(*args, **kwargs):
    return 1


def execute_query(*args, **kwargs):
    return None


secure_exec_mod.execute_command = execute_command
secure_exec_mod.execute_query = execute_query
sys.modules["database.secure_exec"] = secure_exec_mod

# Stub infrastructure.database.secure_query with minimal builder
infrastructure_pkg = types.ModuleType("infrastructure")
infrastructure_pkg.__path__ = []  # type: ignore[attr-defined]
sys.modules["infrastructure"] = infrastructure_pkg
infrastructure_db_pkg = types.ModuleType("infrastructure.database")
infrastructure_db_pkg.__path__ = []  # type: ignore[attr-defined]
sys.modules["infrastructure.database"] = infrastructure_db_pkg
secure_query_mod = types.ModuleType("infrastructure.database.secure_query")


class SecureQueryBuilder:
    def __init__(self, allowed_tables=None, allowed_columns=None, **_):
        self.allowed_tables = allowed_tables or set()
        self.allowed_columns = allowed_columns or set()

    def table(self, name):
        if name not in self.allowed_tables:
            raise ValueError("Unapproved identifier: " + name)
        return name

    def column(self, name):
        if name not in self.allowed_columns:
            raise ValueError("Unapproved identifier: " + name)
        return name

    def build(self, sql, params, logger=None, **_):
        return sql, params


secure_query_mod.SecureQueryBuilder = SecureQueryBuilder
sys.modules["infrastructure.database.secure_query"] = secure_query_mod

# Stub models.compliance to avoid SQLAlchemy dependency
models_mod = types.ModuleType("yosai_intel_dashboard.models.compliance")


class DSARRequest:  # pragma: no cover - placeholder
    pass


class DSARRequestType:  # pragma: no cover - placeholder
    ACCESS = type("Enum", (), {"value": "access"})()


class DSARStatus:  # pragma: no cover - placeholder
    PENDING = type("Enum", (), {"value": "pending"})()
    IN_PROGRESS = type("Enum", (), {"value": "in_progress"})()
    COMPLETED = type("Enum", (), {"value": "completed"})()
    REJECTED = type("Enum", (), {"value": "rejected"})()


models_mod.DSARRequest = DSARRequest
models_mod.DSARRequestType = DSARRequestType
models_mod.DSARStatus = DSARStatus
sys.modules["yosai_intel_dashboard.models.compliance"] = models_mod

# Load dsar_service
import importlib.util
import pathlib

module_path = pathlib.Path(
    "yosai_intel_dashboard/src/adapters/api/plugins/compliance_plugin/services/dsar_service.py"
)
spec = importlib.util.spec_from_file_location("dsar_service", module_path)
ds = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ds)  # type: ignore[arg-type]


def _make_service(monkeypatch, rows: int = 1):
    db = MagicMock()
    audit_logger = MagicMock()
    service = ds.DSARService(db, audit_logger)
    exec_mock = MagicMock(return_value=rows)
    monkeypatch.setattr(ds, "execute_command", exec_mock)
    return service, exec_mock


def test_rectification_rejects_disallowed_columns(monkeypatch):
    service, exec_mock = _make_service(monkeypatch)
    result = service._process_rectification_request(
        "user1", {"updates": {"password": "secret"}}
    )
    assert result is False
    exec_mock.assert_not_called()


def test_rectification_updates_allowed_columns(monkeypatch):
    service, exec_mock = _make_service(monkeypatch)
    result = service._process_rectification_request(
        "user1", {"updates": {"name": "Alice"}}
    )
    assert result is True
    exec_mock.assert_called_once()
