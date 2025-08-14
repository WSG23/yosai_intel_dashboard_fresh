from __future__ import annotations

import importlib.util
import os
import sys
from enum import Enum
from types import ModuleType, SimpleNamespace

import pytest
from flask import Flask

from tests.fixtures import setup_test_environment


def _create_app(monkeypatch, rbac_service):
    """Create Flask app with compliance blueprint and RBAC service."""
    # Stub compliance models
    comp_mod = ModuleType("yosai_intel_dashboard.models.compliance")

    class ConsentType(Enum):
        BIOMETRIC_ACCESS = "biometric_access"

    class DSARRequestType(Enum):
        ACCESS = "access"

    comp_mod.ConsentType = ConsentType
    comp_mod.DSARRequestType = DSARRequestType
    monkeypatch.setitem(
        sys.modules, "yosai_intel_dashboard.models.compliance", comp_mod
    )

    # Stub audit logger
    audit_mod = ModuleType("yosai_intel_dashboard.src.core.audit_logger")

    class DummyAuditLogger:
        def log_action(self, *a, **k):
            pass

        def get_user_audit_trail(self, uid, days):
            return []

    audit_mod.ComplianceAuditLogger = DummyAuditLogger
    monkeypatch.setitem(
        sys.modules, "yosai_intel_dashboard.src.core.audit_logger", audit_mod
    )

    # Minimal container stub
    container_pkg = ModuleType("yosai_intel_dashboard.src.core")
    container_pkg.__path__ = []
    monkeypatch.setitem(sys.modules, "yosai_intel_dashboard.src.core", container_pkg)
    cont_mod = ModuleType("yosai_intel_dashboard.src.core.container")

    class DummyContainer:
        def get(self, name):
            return None

    cont_mod.Container = lambda: DummyContainer()
    monkeypatch.setitem(
        sys.modules, "yosai_intel_dashboard.src.core.container", cont_mod
    )

    # Database exec stub
    db_mod = ModuleType("database.secure_exec")
    db_mod.execute_query = lambda *a, **k: []
    monkeypatch.setitem(sys.modules, "database.secure_exec", db_mod)

    # Error handling stubs
    err_mod = ModuleType("yosai_intel_dashboard.src.error_handling")

    class ErrorCategory(Enum):
        INTERNAL = 1

    class ErrorHandler:
        def handle(self, e, cat):
            return SimpleNamespace(to_dict=lambda: {"error": str(e)})

    err_mod.ErrorCategory = ErrorCategory
    err_mod.ErrorHandler = ErrorHandler
    monkeypatch.setitem(
        sys.modules, "yosai_intel_dashboard.src.error_handling", err_mod
    )

    # Compliance service stubs
    services_pkg = ModuleType("yosai_intel_dashboard.src.services")
    services_pkg.__path__ = []
    monkeypatch.setitem(sys.modules, "yosai_intel_dashboard.src.services", services_pkg)
    comp_pkg = ModuleType("yosai_intel_dashboard.src.services.compliance")
    comp_pkg.__path__ = []
    monkeypatch.setitem(
        sys.modules, "yosai_intel_dashboard.src.services.compliance", comp_pkg
    )
    consent_mod = ModuleType(
        "yosai_intel_dashboard.src.services.compliance.consent_service"
    )
    consent_mod.ConsentService = type("ConsentService", (), {})
    monkeypatch.setitem(
        sys.modules,
        "yosai_intel_dashboard.src.services.compliance.consent_service",
        consent_mod,
    )
    dsar_mod = ModuleType("yosai_intel_dashboard.src.services.compliance.dsar_service")

    class DSARService:
        def get_pending_requests(self, days):
            return [{"due": days}]

    dsar_mod.DSARService = DSARService
    monkeypatch.setitem(
        sys.modules,
        "yosai_intel_dashboard.src.services.compliance.dsar_service",
        dsar_mod,
    )

    # Shared errors and validator stubs
    shared_mod = ModuleType("shared.errors.types")
    shared_mod.ErrorCode = type("ErrorCode", (), {"INTERNAL": 1})
    monkeypatch.setitem(sys.modules, "shared.errors.types", shared_mod)

    yf_mod = ModuleType("yosai_framework.errors")
    yf_mod.CODE_TO_STATUS = {1: 500}
    monkeypatch.setitem(sys.modules, "yosai_framework.errors", yf_mod)

    # Load real RBAC module
    spec = importlib.util.spec_from_file_location(
        "yosai_intel_dashboard.src.core.rbac", "yosai_intel_dashboard/src/core/rbac.py"
    )
    rbac_module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(rbac_module)
    monkeypatch.setitem(sys.modules, "yosai_intel_dashboard.src.core.rbac", rbac_module)

    # services.security.require_role should use RBAC decorator
    sec_mod = ModuleType("yosai_intel_dashboard.src.services.security")
    sec_mod.require_role = rbac_module.require_role
    monkeypatch.setitem(
        sys.modules, "yosai_intel_dashboard.src.services.security", sec_mod
    )

    # flask-login stub
    login_mod = ModuleType("flask_login")
    login_mod.current_user = SimpleNamespace(id="user", is_authenticated=True)
    login_mod.login_required = lambda f: f
    monkeypatch.setitem(sys.modules, "flask_login", login_mod)

    # Import compliance controller
    spec2 = importlib.util.spec_from_file_location(
        "compliance_controller",
        "yosai_intel_dashboard/src/adapters/api/plugins/compliance_plugin/compliance_controller.py",
    )
    module = importlib.util.module_from_spec(spec2)
    assert spec2.loader
    spec2.loader.exec_module(module)

    # Override service retrieval
    dsar_service = DSARService()
    audit_logger = DummyAuditLogger()
    monkeypatch.setattr(
        module, "get_services", lambda: (None, dsar_service, audit_logger)
    )

    app = Flask(__name__)
    app.secret_key = os.urandom(16).hex()
    app.config["RBAC_SERVICE"] = rbac_service
    app.register_blueprint(module.compliance_bp)
    return app, login_mod


class DummyRBACService:
    async def has_role(self, user_id: str, role: str) -> bool:
        return user_id == "admin_user" and role == "admin"


@pytest.mark.integration
def test_rbac_enforces_admin_role(monkeypatch):
    with setup_test_environment():
        app, login_mod = _create_app(monkeypatch, DummyRBACService())
        client = app.test_client()

        # Non-admin user
        login_mod.current_user.id = "regular_user"
        with client.session_transaction() as sess:
            sess["user_id"] = "regular_user"
        resp = client.get("/api/v1/compliance/admin/dsar/pending")
        assert resp.status_code == 403

        # Admin user
        login_mod.current_user.id = "admin_user"
        with client.session_transaction() as sess:
            sess["user_id"] = "admin_user"
        resp = client.get("/api/v1/compliance/admin/dsar/pending")
        assert resp.status_code == 200
