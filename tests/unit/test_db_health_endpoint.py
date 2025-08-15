import importlib.util
from pathlib import Path

from flask import Flask

import factories
import sys
import types

secret_stub = types.SimpleNamespace(validate_secrets=lambda: {})
sys.modules["yosai_intel_dashboard.src.core.secret_manager"] = secret_stub

spec = importlib.util.spec_from_file_location(
    "health_module",
    Path(__file__).resolve().parents[1]
    / "yosai_intel_dashboard"
    / "src"
    / "core"
    / "app_factory"
    / "health.py",
)
health_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(health_module)  # type: ignore
register_health_endpoints = health_module.register_health_endpoints


def test_db_health_endpoint(monkeypatch):
    app = Flask(__name__)
    dummy_status = factories.DBHealthStatus(healthy=True, details={"info": "ok"})
    monkeypatch.setattr(factories, "health_check", lambda: dummy_status)
    monkeypatch.setattr(health_module, "db_health_check", lambda: dummy_status)

    register_health_endpoints(app)
    client = app.test_client()
    resp = client.get("/health/db")
    assert resp.status_code == 200
    assert resp.get_json() == {"healthy": True, "details": {"info": "ok"}}

