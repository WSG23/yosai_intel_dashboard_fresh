import importlib
import os
import sys
import types
from pathlib import Path
from yosai_intel_dashboard.src.core.imports.resolver import safe_import

safe_import('yosai_intel_dashboard', types.ModuleType("yosai_intel_dashboard"))
sys.modules["yosai_intel_dashboard"].__path__ = [str(Path(__file__).resolve().parents[1] / "yosai_intel_dashboard")]

import pytest
from fastapi.testclient import TestClient


class DummyFileProcessor:
    def process_file_async(self, content, filename):
        return "job1"

    def get_job_status(self, job_id):
        return {"status": "done"}


def _create_app(monkeypatch):

    container = types.SimpleNamespace(
        services={"file_processor": DummyFileProcessor()},
        get=lambda key: container.services[key],
        register_singleton=lambda key, value: container.services.__setitem__(
            key, value
        ),
        has=lambda key: key in container.services,
    )
    monkeypatch.setitem(
        sys.modules, "core.container", types.SimpleNamespace(container=container)
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
    monkeypatch.setitem(
        sys.modules, "prometheus_fastapi_instrumentator", prom_stub
    )

    upload_stub = types.ModuleType(
        "yosai_intel_dashboard.src.services.upload_endpoint"
    )
    monkeypatch.setitem(
        sys.modules,
        "yosai_intel_dashboard.src.services.upload_endpoint",
        upload_stub,
    )

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

    adapter = importlib.import_module("api.adapter")
    return adapter.create_api_app()


@pytest.mark.integration
def test_csrf_token_and_protected_endpoint(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", os.urandom(16).hex())
    app = _create_app(monkeypatch)
    client = TestClient(app)

    token_resp = client.get("/v1/csrf-token")
    assert token_resp.status_code == 200
    token = token_resp.json()["csrf_token"]
    assert "HttpOnly" in token_resp.headers.get("set-cookie", "")

    resp = client.post(
        "/v1/upload",
        json={"contents": ["data:text/plain;base64,Zm8="], "filenames": ["t.txt"]},
    )
    assert resp.status_code == 400

    resp = client.post(
        "/v1/upload",
        json={"contents": ["data:text/plain;base64,Zm8="], "filenames": ["t.txt"]},
        headers={"X-CSRFToken": token},
    )
    assert resp.status_code == 202
