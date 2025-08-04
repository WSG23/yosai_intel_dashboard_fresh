import importlib.util
import pathlib
import sys
import types
from datetime import datetime, timezone

from yosai_intel_dashboard.src.core.imports.resolver import safe_import


class DummyAuditLogger:
    def __init__(self) -> None:
        self.calls: list[dict] = []
        self.history: list[dict] = []
        self.search_calls: list[dict] = []

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

    def search_audit_logs(self, **kwargs):
        self.search_calls.append(kwargs)
        results = self.history
        r_type = kwargs.get("resource_type")
        r_id = kwargs.get("resource_id")
        if r_type:
            results = [r for r in results if r.get("resource_type") == r_type]
        if r_id:
            results = [r for r in results if r.get("resource_id") == r_id]
        return results  # intentionally ignore limit to test enforcement


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
        / "feature_flags"
        / "audit.py"
    )
    spec = importlib.util.spec_from_file_location("feature_flags.audit", module_path)
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


def test_get_feature_flag_audit_history_respects_limit(monkeypatch):
    module, dummy = load_module(monkeypatch)

    # Populate history with many entries for two different flags
    dummy.history = [
        {
            "resource_type": "feature_flag",
            "resource_id": "my_flag",
            "idx": i,
        }
        for i in range(10)
    ]
    dummy.history += [
        {
            "resource_type": "feature_flag",
            "resource_id": "other_flag",
            "idx": i,
        }
        for i in range(10)
    ]

    limit = 5
    result = module.get_feature_flag_audit_history("my_flag", limit=limit)

    # Ensure filtering and limiting
    assert len(result) == limit
    assert all(entry["resource_id"] == "my_flag" for entry in result)

    # Ensure search was called with proper filters
    search_call = dummy.search_calls[-1]
    assert search_call["resource_type"] == "feature_flag"
    assert search_call["resource_id"] == "my_flag"
    assert search_call["limit"] == limit
