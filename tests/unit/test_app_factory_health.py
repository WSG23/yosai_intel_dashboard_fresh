import importlib.util
import sys
import types
from dataclasses import dataclass
from pathlib import Path

import pytest

# Create minimal package structure and stub heavy dependencies
root_pkg = types.ModuleType("yosai_intel_dashboard")
src_pkg = types.ModuleType("yosai_intel_dashboard.src")
core_pkg = types.ModuleType("yosai_intel_dashboard.src.core")
app_factory_pkg = types.ModuleType("yosai_intel_dashboard.src.core.app_factory")
for pkg in (root_pkg, src_pkg, core_pkg, app_factory_pkg):
    pkg.__path__ = []
    sys.modules[pkg.__name__] = pkg

secret_stub = types.SimpleNamespace(validate_secrets=lambda: {})
sys.modules["yosai_intel_dashboard.src.core.secret_manager"] = secret_stub
sys.modules["factories"] = types.SimpleNamespace(health_check=lambda: None)

module_path = (
    Path(__file__).resolve().parents[1]
    / "yosai_intel_dashboard"
    / "src"
    / "core"
    / "app_factory"
    / "health.py"
)
spec = importlib.util.spec_from_file_location(
    "yosai_intel_dashboard.src.core.app_factory.health", module_path
)
health = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = health
spec.loader.exec_module(health)  # type: ignore[attr-defined]


@dataclass
class DummyStatus:
    healthy: bool
    details: str = ""

    def model_dump(self) -> dict:
        return {"healthy": self.healthy, "details": self.details}


class FakeServer:
    def __init__(self):
        self.routes = {}

    def route(self, path, methods=None):
        def decorator(func):
            self.routes[(path, tuple(methods or []))] = func
            return func
        return decorator


@pytest.mark.parametrize(
    "db_result,secrets_result,expected",
    [
        (DummyStatus(True), {"valid": True}, (True, None)),
        (DummyStatus(False, "boom"), {"valid": True}, (False, "database unhealthy: boom")),
        (Exception("crash"), {"valid": True}, (False, "database check failed: crash")),
        (DummyStatus(True), {"valid": False, "missing": ["TOKEN"]}, (False, "missing secrets: TOKEN")),
        (DummyStatus(True), {"valid": False}, (False, "secret validation failed")),
        (DummyStatus(True), Exception("oops"), (False, "secret validation failed: oops")),
    ],
)
def test_check_critical_dependencies(monkeypatch, db_result, secrets_result, expected):
    def fake_db():
        if isinstance(db_result, Exception):
            raise db_result
        return db_result

    def fake_secrets():
        if isinstance(secrets_result, Exception):
            raise secrets_result
        return secrets_result

    monkeypatch.setattr(health, "db_health_check", fake_db)
    monkeypatch.setattr(health, "validate_secrets", fake_secrets)

    assert health.check_critical_dependencies() == expected


@pytest.mark.parametrize("healthy", [True, False])
def test_register_health_endpoint_health(monkeypatch, healthy):
    server = FakeServer()
    reason = None if healthy else "bad"
    monkeypatch.setattr(health, "check_critical_dependencies", lambda: (healthy, reason))
    health.register_health_endpoints(server)

    resp = server.routes[("/health", ("GET",))]()
    expected = ({"status": "healthy"}, 200) if healthy else ({"status": "unhealthy", "reason": reason}, 503)
    assert resp == expected


def test_register_health_endpoints_other_routes(monkeypatch):
    server = FakeServer()
    status = DummyStatus(True)
    monkeypatch.setattr(health, "db_health_check", lambda: status)
    monkeypatch.setattr(health, "validate_secrets", lambda: {"ok": True})
    health.register_health_endpoints(server)

    assert server.routes[("/health/db", ("GET",))]() == (status.model_dump(), 200)
    assert server.routes[("/health/secrets", ("GET",))]() == ({"ok": True}, 200)


def test_register_health_endpoints_progress():
    server = FakeServer()
    called = types.SimpleNamespace(task=None)

    class Progress:
        def stream(self, task_id: str):  # pragma: no cover - trivial
            called.task = task_id
            return f"stream {task_id}"

    health.register_health_endpoints(server, Progress())
    route = server.routes[("/upload/progress/<task_id>", ())]
    assert route("abc") == "stream abc"
    assert called.task == "abc"
