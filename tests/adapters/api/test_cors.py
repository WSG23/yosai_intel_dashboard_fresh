import importlib
import sys
import types

import pytest
from fastapi.testclient import TestClient
from tests.import_helpers import safe_import, import_optional

# Provide stubs when optional dependencies are missing
if "flask_wtf" not in sys.modules:
    fw = importlib.import_module("tests.stubs.flask_wtf")
    safe_import('flask_wtf', fw)
    safe_import('flask_wtf.csrf', fw)
if "flask_cors" not in sys.modules:
    safe_import('flask_cors', importlib.import_module("flask_cors"))
if "services" not in sys.modules:
    safe_import('services', importlib.import_module("tests.stubs.services"))


def _create_app(monkeypatch, origins):

    container = types.SimpleNamespace(
        services={
            "file_processor": object(),
            "device_learning_service": object(),
            "upload_processor": object(),
            "consolidated_learning_service": object(),
        },
        get=lambda key: container.services[key],
        register_singleton=lambda key, value: container.services.__setitem__(
            key, value
        ),
        has=lambda key: key in container.services,
    )
    monkeypatch.setitem(
        sys.modules,
        "yosai_intel_dashboard.src.core.container",
        types.SimpleNamespace(container=container),
    )

    class DummyService:
        def __init__(self, name, config_path):
            from fastapi import FastAPI

            self.name = name
            self.app = FastAPI(title=name)
            self.log = types.SimpleNamespace(
                info=lambda *a, **k: None, error=lambda *a, **k: None
            )

        def start(self):
            pass

    monkeypatch.setitem(
        sys.modules,
        "yosai_framework.service",
        types.SimpleNamespace(BaseService=DummyService),
    )

    from flask import Blueprint

    upload_stub = types.ModuleType("yosai_intel_dashboard.src.services.upload_endpoint")
    upload_stub.create_upload_blueprint = lambda *a, **k: Blueprint("upload", __name__)
    device_stub = types.ModuleType("yosai_intel_dashboard.src.services.device_endpoint")
    device_stub.create_device_blueprint = lambda *a, **k: Blueprint("device", __name__)
    mappings_stub = types.ModuleType("yosai_intel_dashboard.src.services.mappings_endpoint")
    mappings_stub.create_mappings_blueprint = lambda *a, **k: Blueprint("mappings", __name__)
    token_stub = types.ModuleType("yosai_intel_dashboard.src.services.token_endpoint")
    token_stub.create_token_blueprint = lambda *a, **k: Blueprint("token", __name__)
    settings_stub = types.ModuleType("settings_endpoint")
    settings_stub.settings_bp = Blueprint("settings", __name__)
    from fastapi import APIRouter
    analytics_stub = types.ModuleType("api.analytics_router")
    analytics_stub.router = APIRouter()
    analytics_stub.init_cache_manager = lambda: None
    monitoring_stub = types.ModuleType("api.monitoring_router")
    monitoring_stub.router = APIRouter()
    for name, mod in {
        "yosai_intel_dashboard.src.services.upload_endpoint": upload_stub,
        "yosai_intel_dashboard.src.services.device_endpoint": device_stub,
        "yosai_intel_dashboard.src.services.mappings_endpoint": mappings_stub,
        "yosai_intel_dashboard.src.services.token_endpoint": token_stub,
        "settings_endpoint": settings_stub,
        "api.analytics_router": analytics_stub,
        "api.monitoring_router": monitoring_stub,
    }.items():
        monkeypatch.setitem(sys.modules, name, mod)

    monkeypatch.setitem(
        sys.modules,
        "yosai_intel_dashboard.src.core.secrets_validator",
        types.SimpleNamespace(validate_all_secrets=lambda: None),
    )
    monkeypatch.setitem(
        sys.modules,
        "yosai_intel_dashboard.src.core.rbac",
        types.SimpleNamespace(RBACService=object, create_rbac_service=lambda: None),
    )
    monkeypatch.setitem(
        sys.modules,
        "yosai_intel_dashboard.src.services.security",
        types.SimpleNamespace(
            verify_service_jwt=lambda token: True,
            require_token=lambda f: f,
        ),
    )

    monkeypatch.setitem(
        sys.modules,
        "yosai_intel_dashboard.src.infrastructure.config",
        types.SimpleNamespace(
            get_security_config=lambda: types.SimpleNamespace(cors_origins=origins),
            get_cache_config=lambda: types.SimpleNamespace(ttl=0),
        ),
    )
    monkeypatch.setitem(
        sys.modules,
        "yosai_intel_dashboard.src.infrastructure.config.constants",
        types.SimpleNamespace(API_PORT=8000),
    )

    adapter = importlib.import_module("api.adapter")
    return adapter.create_api_app()


@pytest.mark.unit
def test_allowed_origin(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "test")
    app = _create_app(monkeypatch, ["https://allowed.com"])
    client = TestClient(app)
    resp = client.get("/v1/csrf-token", headers={"Origin": "https://allowed.com"})
    assert resp.headers.get("access-control-allow-origin") == "https://allowed.com"


@pytest.mark.unit
def test_blocked_origin(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "test")
    app = _create_app(monkeypatch, ["https://allowed.com"])
    client = TestClient(app)
    resp = client.get("/v1/csrf-token", headers={"Origin": "https://other.com"})
    assert "access-control-allow-origin" not in resp.headers
