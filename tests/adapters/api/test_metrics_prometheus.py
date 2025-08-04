import importlib
import os
import sys
import types

import pytest
from fastapi.testclient import TestClient


def _create_app(monkeypatch):
    file_processor = types.SimpleNamespace(
        process_file_async=lambda content, filename: "job1",
        get_job_status=lambda job_id: "done",
        validator=types.SimpleNamespace(
            validate_file_upload=lambda filename, data: None
        ),
    )
    file_handler = types.SimpleNamespace(
        validator=types.SimpleNamespace(validate_file_upload=lambda *a, **k: None)
    )
    container = types.SimpleNamespace(
        services={"file_processor": file_processor, "file_handler": file_handler},
        get=lambda key: container.services[key],
        register_singleton=lambda key, value: container.services.__setitem__(key, value),
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

        def _add_health_routes(self):
            pass

    monkeypatch.setitem(
        sys.modules,
        "yosai_framework.service",
        types.SimpleNamespace(BaseService=DummyService),
    )

    from fastapi import APIRouter

    analytics_stub = types.ModuleType("api.analytics_router")
    analytics_stub.router = APIRouter()
    analytics_stub.init_cache_manager = lambda: None
    monitoring_stub = types.ModuleType("api.monitoring_router")
    monitoring_stub.router = APIRouter()
    explanations_stub = types.ModuleType("api.explanations")
    explanations_stub.router = APIRouter()
    feature_stub = types.ModuleType("api.routes.feature_flags")
    feature_stub.router = APIRouter()
    for name, mod in {
        "api.analytics_router": analytics_stub,
        "api.monitoring_router": monitoring_stub,
        "api.explanations": explanations_stub,
        "api.routes.feature_flags": feature_stub,
    }.items():
        monkeypatch.setitem(sys.modules, name, mod)

    upload_upload_stub = types.ModuleType(
        "yosai_intel_dashboard.src.services.upload.upload_endpoint"
    )
    from pydantic import BaseModel

    class UploadRequestSchema(BaseModel):
        contents: list[str] | None = None
        filenames: list[str] | None = None

    class UploadResponseSchema(BaseModel):
        job_id: str

    class StatusSchema(BaseModel):
        status: str

    upload_upload_stub.UploadRequestSchema = UploadRequestSchema
    upload_upload_stub.UploadResponseSchema = UploadResponseSchema
    upload_upload_stub.StatusSchema = StatusSchema
    monkeypatch.setitem(
        sys.modules,
        "yosai_intel_dashboard.src.services.upload.upload_endpoint",
        upload_upload_stub,
    )

    settings_stub = types.ModuleType("api.settings_endpoint")

    class _SettingsSchema(BaseModel):
        pass

    settings_stub.SettingsSchema = _SettingsSchema
    settings_stub._load_settings = lambda: {}
    settings_stub._save_settings = lambda data: None
    monkeypatch.setitem(sys.modules, "api.settings_endpoint", settings_stub)

    monkeypatch.setitem(
        sys.modules,
        "yosai_intel_dashboard.src.core.secrets_validator",
        types.SimpleNamespace(validate_all_secrets=lambda: None),
    )
    monkeypatch.setitem(
        sys.modules,
        "yosai_intel_dashboard.src.core.rbac",
        types.SimpleNamespace(create_rbac_service=lambda: None),
    )
    monkeypatch.setitem(
        sys.modules,
        "yosai_intel_dashboard.src.services.security",
        types.SimpleNamespace(
            verify_service_jwt=lambda token: True,
            require_token=lambda f: f,
            require_permission=lambda *a, **k: (lambda f: f),
        ),
    )
    monkeypatch.setitem(
        sys.modules,
        "yosai_intel_dashboard.src.infrastructure.config",
        types.SimpleNamespace(get_security_config=lambda: types.SimpleNamespace(cors_origins=["*"])),
    )
    monkeypatch.setitem(
        sys.modules,
        "yosai_intel_dashboard.src.infrastructure.config.constants",
        types.SimpleNamespace(API_PORT=8000),
    )

    rate_limit_stub = types.ModuleType("middleware.rate_limit")
    from starlette.middleware.base import BaseHTTPMiddleware

    class DummyLimiter:
        def __init__(self, *a, **k):
            pass

        def hit(self, user, ip, tier="default"):
            return {"allowed": True, "limit": 100, "remaining": 100, "retry_after": None}

    class RateLimitMiddleware(BaseHTTPMiddleware):
        def __init__(self, app, limiter, **_):
            super().__init__(app)

        async def dispatch(self, request, call_next):
            return await call_next(request)

    rate_limit_stub.RedisRateLimiter = DummyLimiter
    rate_limit_stub.RateLimitMiddleware = RateLimitMiddleware
    monkeypatch.setitem(sys.modules, "middleware.rate_limit", rate_limit_stub)

    perf_stub = types.ModuleType("monitoring.performance_profiler")
    from contextlib import contextmanager

    class DummyProfiler:
        @contextmanager
        def profile_endpoint(self, endpoint):
            yield

    perf_stub.PerformanceProfiler = DummyProfiler
    monkeypatch.setitem(sys.modules, "monitoring.performance_profiler", perf_stub)

    prom_stub = types.ModuleType("prometheus_fastapi_instrumentator")
    from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
    from fastapi import Response

    class DummyInstr:
        def instrument(self, app):
            return self

        def expose(self, app):
            @app.get("/metrics")
            def _metrics():
                return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

            return self

    prom_stub.Instrumentator = lambda: DummyInstr()
    monkeypatch.setitem(sys.modules, "prometheus_fastapi_instrumentator", prom_stub)

    # redis module is provided via tests.config stub

    adapter = importlib.import_module("api.adapter")
    return adapter.create_api_app()


@pytest.mark.unit
def test_metrics_endpoint_records_upload(monkeypatch):
    monkeypatch.setenv(
        "SECRET_KEY",
        os.environ.get("SECRET_KEY", os.urandom(16).hex()),
    )
    app = _create_app(monkeypatch)
    client = TestClient(app)

    csrf = client.get("/v1/csrf-token").json()["csrf_token"]
    files = {"files": ("t.txt", b"hello", "text/plain")}
    resp = client.post(
        "/v1/upload",
        files=files,
        headers={"X-CSRFToken": csrf},
    )
    assert resp.status_code == 202

    metrics = client.get("/metrics").text
    assert "api_upload_files_total" in metrics
