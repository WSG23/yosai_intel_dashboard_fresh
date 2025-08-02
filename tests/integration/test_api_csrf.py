import importlib
import os
import sys
import types
from pathlib import Path
from tests.import_helpers import safe_import, import_optional

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

    import yosai_intel_dashboard.src.services.upload_endpoint  # ensure module available

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
