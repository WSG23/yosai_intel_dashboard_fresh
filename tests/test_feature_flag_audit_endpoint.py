from __future__ import annotations

import importlib
import sys
import types
from datetime import datetime, timezone

from fastapi import FastAPI


def _prepare_stubs() -> None:
    """Insert lightweight service stubs to satisfy imports."""

    src_pkg = types.ModuleType("yosai_intel_dashboard.src")
    src_pkg.__path__ = []
    sys.modules.setdefault("yosai_intel_dashboard.src", src_pkg)

    services_pkg = types.ModuleType("yosai_intel_dashboard.src.services")
    services_pkg.__path__ = []
    sys.modules.setdefault("yosai_intel_dashboard.src.services", services_pkg)

    feature_flags_mod = types.ModuleType(
        "yosai_intel_dashboard.src.services.feature_flags"
    )
    feature_flags_mod.feature_flags = types.SimpleNamespace(get_all=lambda: {}, _flags={})
    sys.modules[
        "yosai_intel_dashboard.src.services.feature_flags"
    ] = feature_flags_mod

    security_mod = types.ModuleType("yosai_intel_dashboard.src.services.security")
    security_mod.require_role = lambda role: (lambda: None)
    sys.modules["yosai_intel_dashboard.src.services.security"] = security_mod


def test_audit_history_serialization(monkeypatch):
    _prepare_stubs()
    sys.modules.pop("httpx", None)
    from fastapi.testclient import TestClient

    module = importlib.import_module("api.routes.feature_flags")

    ts = datetime(2024, 1, 1, tzinfo=timezone.utc)
    expected_ts = ts.isoformat().replace("+00:00", "Z")
    history = [
        {
            "actor_user_id": "user1",
            "old_value": None,
            "new_value": True,
            "reason": "init",
            "metadata": {"source": "test"},
            "timestamp": ts,
        }
    ]
    module.feature_flag_audit = types.SimpleNamespace(
        get_feature_flag_audit_history=lambda name: history
    )

    app = FastAPI()
    app.include_router(module.router)
    client = TestClient(app)

    resp = client.get("/feature-flags/my_flag/audit")
    assert resp.status_code == 200
    assert resp.json() == {
        "history": [
            {
                "actor_user_id": "user1",
                "old_value": None,
                "new_value": True,
                "reason": "init",
                "metadata": {"source": "test"},
                "timestamp": expected_ts,
            }
        ]
    }
