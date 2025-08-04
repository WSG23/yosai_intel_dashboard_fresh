from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from yosai_intel_dashboard.src.core.imports.resolver import safe_import


def _load_compliance_plugin(monkeypatch, db_success=True, services_success=True):
    path = Path("plugins/compliance_plugin/plugin.py")
    spec = importlib.util.spec_from_file_location(
        "plugins.compliance_plugin.plugin", path
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module

    base_mod = types.ModuleType("core.plugins.base")

    class BasePlugin:
        def __init__(self):
            pass

    base_mod.BasePlugin = BasePlugin
    safe_import('core.plugins.base', base_mod)

    db = MagicMock()
    db.ensure_schema.return_value = db_success
    monkeypatch.setitem(
        sys.modules, "plugins.compliance_plugin.database", types.ModuleType("db")
    )
    sys.modules["plugins.compliance_plugin.database"].ComplianceDatabase = (
        lambda conn: db
    )

    services = MagicMock()
    services.initialize.return_value = services_success
    monkeypatch.setitem(
        sys.modules, "plugins.compliance_plugin.services", types.ModuleType("svc")
    )
    sys.modules["plugins.compliance_plugin.services"].ComplianceServices = (
        lambda c, cfg: services
    )

    monkeypatch.setitem(
        sys.modules, "plugins.compliance_plugin.api", types.ModuleType("api")
    )
    sys.modules["plugins.compliance_plugin.api"].ComplianceAPI = lambda c, cfg: None
    monkeypatch.setitem(
        sys.modules, "plugins.compliance_plugin.middleware", types.ModuleType("mw")
    )
    sys.modules["plugins.compliance_plugin.middleware"].ComplianceMiddleware = (
        lambda c, cfg: None
    )

    spec.loader.exec_module(module)
    return module.CompliancePlugin, db, services


def test_initialize_database_failure(monkeypatch, caplog, mock_auth_env):
    CompliancePlugin, db, services = _load_compliance_plugin(
        monkeypatch, db_success=False
    )
    container = MagicMock()
    container.get.return_value = "db_conn"
    container.register = MagicMock()
    plugin = CompliancePlugin()
    with caplog.at_level("ERROR"):
        result = plugin.initialize(container, {})

    assert result is False
    assert not plugin.is_initialized
    assert not plugin.is_database_ready
    assert any(
        "Failed to initialize compliance database schema" in r.getMessage()
        for r in caplog.records
    )
