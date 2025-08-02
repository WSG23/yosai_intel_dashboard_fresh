import importlib.util
import sys
from enum import Enum
from types import ModuleType, SimpleNamespace

from flask import Flask


def _create_client(monkeypatch):
    # Stub enums to avoid heavy model imports
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
    monkeypatch.setitem(
        sys.modules, "plugins.compliance_plugin.models.compliance", comp_mod
    )

    # Minimal stubs for external dependencies
    audit_mod = ModuleType("core.audit_logger")

    class DummyAuditLogger:
        def log_action(self, *a, **k):
            pass

        def get_user_audit_trail(self, uid, days):
            return [{"uid": uid, "days": days}]

    audit_mod.ComplianceAuditLogger = DummyAuditLogger
    monkeypatch.setitem(sys.modules, "core.audit_logger", audit_mod)

    cont_mod = ModuleType("core.container")

    class DummyContainer:
        def get(self, name):
            return None

    cont_mod.Container = lambda: DummyContainer()
    monkeypatch.setitem(sys.modules, "core.container", cont_mod)
    monkeypatch.setitem(sys.modules, "core.rbac", ModuleType("core.rbac"))
    sys.modules["core.rbac"].require_role = lambda role: (lambda f: f)
    monkeypatch.setitem(
        sys.modules, "services.security", ModuleType("services.security")
    )
    sys.modules["services.security"].require_role = lambda role: (lambda f: f)
    exec_mod = ModuleType("services.database.secure_exec")
    exec_mod.execute_query = lambda *a, **k: []
    monkeypatch.setitem(sys.modules, "services.database.secure_exec", exec_mod)

    err_mod = ModuleType("error_handling")
    err_mod.ErrorCategory = type("ErrorCategory", (), {"INTERNAL": 1})

    class ErrorHandler:
        def handle(self, e, cat):
            return SimpleNamespace(to_dict=lambda: {"error": str(e)})

    err_mod.ErrorHandler = ErrorHandler
    monkeypatch.setitem(sys.modules, "error_handling", err_mod)

    consent_mod = ModuleType("svc.c")
    consent_mod.ConsentService = type("ConsentService", (), {})
    monkeypatch.setitem(sys.modules, "services.compliance.consent_service", consent_mod)
    dsar_mod = ModuleType("svc.dsar")

    class DSARService:
        def get_pending_requests(self, days):
            return [{"due": days}]

    dsar_mod.DSARService = DSARService
    monkeypatch.setitem(sys.modules, "services.compliance.dsar_service", dsar_mod)

    shared_mod = ModuleType("shared.errors.types")
    shared_mod.ErrorCode = type("ErrorCode", (), {"INTERNAL": 1})
    monkeypatch.setitem(sys.modules, "shared.errors.types", shared_mod)

    val_mod = ModuleType("validation.security_validator")

    class SecurityValidator:
        def validate_input(self, value, name=""):
            return {"valid": True, "sanitized": value}

    val_mod.SecurityValidator = SecurityValidator
    monkeypatch.setitem(sys.modules, "validation.security_validator", val_mod)

    yosai_mod = ModuleType("yosai_framework.errors")
    yosai_mod.CODE_TO_STATUS = {1: 500}
    monkeypatch.setitem(sys.modules, "yosai_framework.errors", yosai_mod)

    login_mod = ModuleType("flask_login")
    login_mod.current_user = SimpleNamespace(id="user1", is_authenticated=True)
    login_mod.login_required = lambda f: f
    monkeypatch.setitem(sys.modules, "flask_login", login_mod)

    spec = importlib.util.spec_from_file_location(
        "plugins.compliance_plugin.compliance_controller",
        "plugins/compliance_plugin/compliance_controller.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)

    # Override service retrieval
    dsar_service = DSARService()
    audit_logger = DummyAuditLogger()
    monkeypatch.setattr(
        module, "get_services", lambda: (None, dsar_service, audit_logger)
    )

    app = Flask(__name__)
    app.register_blueprint(module.compliance_bp)
    return app.test_client()


def test_pending_requests_invalid_param(monkeypatch):
    client = _create_client(monkeypatch)
    resp = client.get(
        "/v1/compliance/admin/dsar/pending",
        query_string={"due_within_days": "<script>"},
    )
    assert resp.status_code == 200
    assert resp.get_json()["due_within_days"] == 7


def test_audit_trail_invalid_param(monkeypatch):
    client = _create_client(monkeypatch)
    resp = client.get("/v1/compliance/audit/my-data", query_string={"days": "<script>"})
    assert resp.status_code == 200
    assert resp.get_json()["period_days"] == 30
