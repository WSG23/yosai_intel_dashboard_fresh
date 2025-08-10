import importlib
import logging
import sys
import types
import pytest

# Ensure dependent modules can be imported in minimal environment
sys.modules.setdefault("controllers", types.ModuleType("controllers"))
sys.modules["controllers.compliance_controller"] = types.SimpleNamespace(
    register_compliance_routes=lambda *a, **k: None
)

# Robust import of audit_decorator
try:  # pragma: no cover - attempt full path import
    from yosai_intel_dashboard.src.adapters.api.plugins.compliance_plugin.compliance_setup import (
        audit_decorator,
    )
except Exception:  # pragma: no cover - fallback for alternate layouts
    from adapters.api.plugins.compliance_plugin.compliance_setup import audit_decorator


def test_audit_decorator_logs_failure(monkeypatch, caplog):
    """Decorator should log audit failures and re-raise original error."""

    class BoomAuditLogger:
        def log_action(self, *args, **kwargs):
            raise RuntimeError("audit boom")

    class DummyContainer:
        def get(self, name):
            assert name == "audit_logger"
            return BoomAuditLogger()

    # Patch Container used within the decorator to return our failing logger
    try:
        container_module = importlib.import_module(
            "yosai_intel_dashboard.src.core.container"
        )
    except Exception:  # pragma: no cover
        container_module = importlib.import_module("core.container")

    monkeypatch.setattr(container_module, "Container", lambda: DummyContainer())

    # Provide a dummy current_user for flask_login
    dummy_user = types.SimpleNamespace(is_authenticated=False, id="u1")
    sys.modules["flask_login"] = types.SimpleNamespace(current_user=dummy_user)

    @audit_decorator("TEST", "resource")
    def failing_func():
        raise ValueError("boom")

    with pytest.raises(ValueError):
        with caplog.at_level(logging.ERROR):
            failing_func()

    assert "Audit logging in decorator failed" in caplog.text
