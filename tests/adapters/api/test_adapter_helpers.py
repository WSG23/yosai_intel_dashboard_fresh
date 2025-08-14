from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient
import types
import sys

# Provide pydantic ConfigDict for environments with Pydantic v1
import pydantic

if not hasattr(pydantic, "ConfigDict"):
    class ConfigDict(dict):
        pass

    pydantic.ConfigDict = ConfigDict

# Stub external routers to avoid heavy imports
analytics_router = APIRouter()

@analytics_router.get("/analytics/patterns")
def _patterns():
    return {}

explanations_router = APIRouter()
monitoring_router = APIRouter()
feature_flags_router = APIRouter()

module_stub = types.ModuleType("analytics_router")
module_stub.router = analytics_router
module_stub.init_cache_manager = lambda: None
sys.modules["api.analytics_router"] = module_stub
sys.modules["api.explanations"] = types.SimpleNamespace(router=explanations_router)
sys.modules["api.monitoring_router"] = types.SimpleNamespace(router=monitoring_router)
sys.modules["api.routes.feature_flags"] = types.SimpleNamespace(router=feature_flags_router)

from yosai_intel_dashboard.src.adapters.api.adapter import (
    _configure_app,
    _register_routes,
    _register_upload_endpoints,
    _setup_security,
)


class DummyService:
    def __init__(self):
        self.app: FastAPI | None = None
        self.log = types.SimpleNamespace(error=lambda *a, **k: None)

    def _add_health_routes(self) -> None:
        pass

    def start(self) -> None:
        pass


def _middleware_names(app: FastAPI) -> list[str]:
    return [m.cls.__name__ for m in app.user_middleware]


def test_configure_app_adds_middlewares():
    service = DummyService()
    build_dir = _configure_app(service)
    mws = _middleware_names(service.app)
    assert "TimingMiddleware" in mws
    assert "RateLimitMiddleware" in mws
    assert build_dir.name == "build"


def test_setup_security_sets_secret(monkeypatch):
    service = DummyService()
    _configure_app(service)
    monkeypatch.setenv("SECRET_KEY", "test")
    serializer, _ = _setup_security(service)
    mws = _middleware_names(service.app)
    assert "SecurityHeadersMiddleware" in mws
    assert "CORSMiddleware" in mws
    assert service.app.state.secret_key == "test"
    assert serializer.dumps("ok")


def test_register_routes_adds_versioned_paths(monkeypatch):
    service = DummyService()
    build_dir = _configure_app(service)
    monkeypatch.setenv("SECRET_KEY", "test")
    serializer, add_dep = _setup_security(service)
    monkeypatch.setattr(
        "yosai_intel_dashboard.src.services.auth.require_service_token",
        lambda: None,
    )
    _register_routes(service, build_dir, add_dep)
    paths = {r.path for r in service.app.routes}
    assert "/api/v1/analytics/patterns" in paths
    assert "/analytics/patterns" in paths

    client = TestClient(service.app)
    resp = client.get("/analytics/patterns")
    assert resp.headers["Warning"].startswith("299")


def test_register_upload_endpoints(monkeypatch):
    service = DummyService()
    _configure_app(service)
    monkeypatch.setenv("SECRET_KEY", "test")
    serializer, add_dep = _setup_security(service)

    class DummyValidator:
        def validate_file_upload(self, filename, content):
            return True

    class DummyFileProcessor:
        validator = DummyValidator()

        def process_file_async(self, content, filename):
            return "job"

        def get_job_status(self, job_id):
            return {"state": "ok"}

    from yosai_intel_dashboard.src.core.container import container

    monkeypatch.setattr(container, "get", lambda name: DummyFileProcessor())
    monkeypatch.setattr(container, "has", lambda name: False)

    _register_upload_endpoints(service, serializer, add_dep)

    paths = {r.path for r in service.app.routes}
    assert "/api/v1/upload" in paths

    client = TestClient(service.app)
    resp = client.get("/api/v1/csrf-token")
    assert resp.status_code == 200
    assert "csrf_token" in resp.json()
    legacy = client.get("/csrf-token")
    assert legacy.headers["Warning"].startswith("299")
