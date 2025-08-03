import importlib.util
import pathlib
import sys
import types
from datetime import datetime, timezone

from tests.import_helpers import safe_import


class DummyAuditLogger:
    def __init__(self) -> None:
        self.calls: list[dict] = []
        self.history: list[dict] = []

    # capture any of the specialized logging methods or generic log_action
    def log_feature_flag_created(self, **kwargs):
        self.calls.append(kwargs)
        self.history.append(kwargs)

    def log_feature_flag_updated(self, **kwargs):
        self.calls.append(kwargs)
        self.history.append(kwargs)

    def log_feature_flag_deleted(self, **kwargs):
        self.calls.append(kwargs)
        self.history.append(kwargs)

    def log_action(self, **kwargs):  # fallback if implementation uses log_action
        self.calls.append(kwargs)
        self.history.append(kwargs)

    def get_feature_flag_audit_history(self, name: str):
        return self.history


def load_module(monkeypatch):
    dummy = DummyAuditLogger()
    audit_mod = types.ModuleType("core.audit_logger")
    audit_mod.ComplianceAuditLogger = lambda *a, **k: dummy
    safe_import("core.audit_logger", lambda: audit_mod)
    # Also cover fully-qualified import paths
    monkeypatch.setitem(
        sys.modules, "yosai_intel_dashboard.src.core.audit_logger", audit_mod
    )

    module_path = (
        pathlib.Path(__file__).resolve().parents[1]
        / "yosai_intel_dashboard"
        / "src"
        / "services"
        / "feature_flag_audit.py"
    )
    spec = importlib.util.spec_from_file_location("feature_flag_audit", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if hasattr(module, "audit_logger"):
        module.audit_logger = dummy
    return module, dummy


def test_log_feature_flag_created(monkeypatch):
    module, dummy = load_module(monkeypatch)
    ts = datetime.now(timezone.utc)
    module.log_feature_flag_created(
        "my_flag", new_value=True, actor_user_id="user1", reason="initial", timestamp=ts
    )
    entry = dummy.calls[-1]
    assert entry["actor_user_id"] == "user1"
    assert entry.get("old_value") in (None, entry.get("metadata", {}).get("old_value"))
    new_val = entry.get("new_value") or entry.get("metadata", {}).get("new_value")
    assert new_val is True
    assert (
        entry.get("reason")
        or entry.get("metadata", {}).get("reason")
    ) == "initial"
    ts_logged = entry.get("timestamp") or entry.get("metadata", {}).get("timestamp")
    assert ts_logged == ts


def test_log_feature_flag_updated(monkeypatch):
    module, dummy = load_module(monkeypatch)
    ts = datetime.now(timezone.utc)
    module.log_feature_flag_updated(
        "my_flag", old_value=False, new_value=True, actor_user_id="user2", reason="update", timestamp=ts
    )
    entry = dummy.calls[-1]
    assert entry["actor_user_id"] == "user2"
    assert (
        entry.get("old_value")
        or entry.get("metadata", {}).get("old_value")
    ) is False
    new_val = entry.get("new_value") or entry.get("metadata", {}).get("new_value")
    assert new_val is True
    assert (
        entry.get("reason")
        or entry.get("metadata", {}).get("reason")
    ) == "update"
    ts_logged = entry.get("timestamp") or entry.get("metadata", {}).get("timestamp")
    assert ts_logged == ts


def test_log_feature_flag_deleted(monkeypatch):
    module, dummy = load_module(monkeypatch)
    ts = datetime.now(timezone.utc)
    module.log_feature_flag_deleted(
        "my_flag", old_value=True, actor_user_id="user3", reason="cleanup", timestamp=ts
    )
    entry = dummy.calls[-1]
    assert entry["actor_user_id"] == "user3"
    assert (
        entry.get("old_value")
        or entry.get("metadata", {}).get("old_value")
    ) is True
    new_val = entry.get("new_value") or entry.get("metadata", {}).get("new_value")
    assert new_val in (None, False)
    assert (
        entry.get("reason")
        or entry.get("metadata", {}).get("reason")
    ) == "cleanup"
    ts_logged = entry.get("timestamp") or entry.get("metadata", {}).get("timestamp")
    assert ts_logged == ts


def test_get_feature_flag_audit_history(monkeypatch):
    module, dummy = load_module(monkeypatch)
    dummy.history = [
        {
            "actor_user_id": "user1",
            "old_value": None,
            "new_value": True,
            "reason": "initial",
            "timestamp": datetime.now(timezone.utc),
        }
    ]
    assert module.get_feature_flag_audit_history("my_flag") == dummy.history
