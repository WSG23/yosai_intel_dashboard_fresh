from __future__ import annotations

import importlib
import os
import sys
import types

sys.meta_path = [
    m for m in sys.meta_path if m.__class__.__name__ != "_MissingModuleFinder"
]
sys.modules.pop("pydantic", None)
sys.modules.pop("starlette", None)
sys.modules.pop("starlette.websockets", None)
import pydantic as pydantic_real
import starlette.websockets as _starlette_websockets

sys.modules["pydantic"] = pydantic_real
sys.modules["starlette.websockets"] = _starlette_websockets

sys.modules.setdefault("flask_cors", types.ModuleType("flask_cors"))
sys.modules.setdefault("aiofiles", types.ModuleType("aiofiles"))

import pytest
from fastapi.testclient import TestClient

from yosai_intel_dashboard.src.core.imports.resolver import safe_import

# Provide stubs when optional dependencies are missing
fw = importlib.import_module("tests.stubs.flask_wtf")
sys.modules.setdefault("flask_wtf", fw)
sys.modules.setdefault("flask_wtf.csrf", fw)
if "flask_cors" not in sys.modules:
    safe_import("flask_cors", importlib.import_module("flask_cors"))
if "services" not in sys.modules:
    safe_import("services", importlib.import_module("tests.stubs.services"))


def _create_app(monkeypatch, origins):
    import pydantic as pydantic_real
    from pydantic import BaseModel

    monkeypatch.setitem(sys.modules, "pydantic", pydantic_real)

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

    prom_stub = types.ModuleType("prometheus_fastapi_instrumentator")

    class DummyInstr:
        def instrument(self, app):
            return self

        def expose(self, app):
            from fastapi import Response
            from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

            @app.get("/metrics")
            def _metrics():
                return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

            return self

    prom_stub.Instrumentator = lambda: DummyInstr()
    monkeypatch.setitem(sys.modules, "prometheus_fastapi_instrumentator", prom_stub)

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

        def _add_health_routes(self):
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
    mappings_stub = types.ModuleType(
        "yosai_intel_dashboard.src.services.mappings_endpoint"
    )
    mappings_stub.create_mappings_blueprint = lambda *a, **k: Blueprint(
        "mappings", __name__
    )
    token_stub = types.ModuleType("yosai_intel_dashboard.src.services.token_endpoint")
    token_stub.create_token_blueprint = lambda *a, **k: Blueprint("token", __name__)
    settings_stub = types.ModuleType("api.settings_endpoint")

    class _SettingsSchema(BaseModel):
        pass

    settings_stub.SettingsSchema = _SettingsSchema
    settings_stub._load_settings = lambda: {}
    settings_stub._save_settings = lambda data: None
    from fastapi import APIRouter

    analytics_stub = types.ModuleType("api.analytics_router")
    analytics_stub.router = APIRouter()
    analytics_stub.init_cache_manager = lambda: None
    monitoring_stub = types.ModuleType("api.monitoring_router")
    monitoring_stub.router = APIRouter()
    explanations_stub = types.ModuleType("api.explanations")
    explanations_stub.router = APIRouter()
    upload_upload_stub = types.ModuleType(
        "yosai_intel_dashboard.src.services.upload.upload_endpoint"
    )
    from pydantic import BaseModel

    class UploadRequestSchema(BaseModel):
        contents: list[str] | None = None
        filenames: list[str] | None = None

    class UploadResponseSchema(BaseModel):
        results: list[str]

    upload_upload_stub.UploadRequestSchema = UploadRequestSchema
    upload_upload_stub.UploadResponseSchema = UploadResponseSchema
    for name, mod in {
        "yosai_intel_dashboard.src.services.upload_endpoint": upload_stub,
        "yosai_intel_dashboard.src.services.upload.upload_endpoint": upload_upload_stub,
        "yosai_intel_dashboard.src.services.device_endpoint": device_stub,
        "yosai_intel_dashboard.src.services.mappings_endpoint": mappings_stub,
        "yosai_intel_dashboard.src.services.token_endpoint": token_stub,
        "api.settings_endpoint": settings_stub,
        "api.analytics_router": analytics_stub,
        "api.monitoring_router": monitoring_stub,
        "api.explanations": explanations_stub,
    }.items():
        monkeypatch.setitem(sys.modules, name, mod)

    monkeypatch.setitem(
        sys.modules,
        "yosai_intel_dashboard.src.core.secrets_validator",
        types.SimpleNamespace(validate_all_secrets=lambda: None),
    )

    async def _rbac_stub():
        return None

    monkeypatch.setitem(
        sys.modules,
        "yosai_intel_dashboard.src.core.rbac",
        types.SimpleNamespace(RBACService=object, create_rbac_service=_rbac_stub),
    )
    security_mod = types.ModuleType("yosai_intel_dashboard.src.services.security")
    security_mod.verify_service_jwt = lambda token: True
    security_mod.require_token = lambda f: f
    security_mod.require_permission = lambda *a, **k: (lambda f: f)
    security_mod.__path__ = []
    monkeypatch.setitem(
        sys.modules, "yosai_intel_dashboard.src.services.security", security_mod
    )
    monkeypatch.setitem(
        sys.modules,
        "yosai_intel_dashboard.src.services.security.jwt_service",
        types.ModuleType("jwt_service"),
    )

    config_mod = types.ModuleType("yosai_intel_dashboard.src.infrastructure.config")
    config_mod.get_security_config = lambda: types.SimpleNamespace(cors_origins=origins)
    config_mod.get_cache_config = lambda: types.SimpleNamespace(ttl=0)
    config_mod.__path__ = []
    monkeypatch.setitem(
        sys.modules, "yosai_intel_dashboard.src.infrastructure.config", config_mod
    )
    loader_mod = types.ModuleType("loader")
    loader_mod.ConfigurationLoader = object
    monkeypatch.setitem(
        sys.modules,
        "yosai_intel_dashboard.src.infrastructure.config.loader",
        loader_mod,
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
    monkeypatch.setenv(
        "SECRET_KEY",
        os.environ.get("SECRET_KEY", os.urandom(16).hex()),
    )
    app = _create_app(monkeypatch, ["https://allowed.com"])
    client = TestClient(app)
    resp = client.get("/v1/csrf-token", headers={"Origin": "https://allowed.com"})
    assert resp.headers.get("access-control-allow-origin") == "https://allowed.com"


@pytest.mark.unit
def test_blocked_origin(monkeypatch):
    monkeypatch.setenv(
        "SECRET_KEY",
        os.environ.get("SECRET_KEY", os.urandom(16).hex()),
    )
    app = _create_app(monkeypatch, ["https://allowed.com"])
    client = TestClient(app)
    resp = client.get("/v1/csrf-token", headers={"Origin": "https://other.com"})
    assert "access-control-allow-origin" not in resp.headers
