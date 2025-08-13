from __future__ import annotations

import time
import types
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import AsyncMock

import httpx
import joblib
import pytest
from jose import jwt


class Dummy:
    def predict(self, data):
        return [len(data)]


@pytest.mark.asyncio
async def test_health_endpoints(app_factory):
    module, _, _ = app_factory()
    transport = httpx.ASGITransport(app=module.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

        resp = await client.get("/api/v1/health/live")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

        resp = await client.get("/api/v1/health/startup")
        assert resp.status_code == 200
        assert resp.json() == {"status": "complete"}

        resp = await client.get("/api/v1/health/ready")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ready"}


@pytest.mark.asyncio
async def test_dashboard_summary_endpoint():
    module, queries_stub, dummy_service = load_app()
    from services.auth import verify_jwt_token

    token = jwt.encode(
        {"sub": "svc", "iss": "gateway", "exp": int(time.time()) + 60},
        "secret",
        algorithm="HS256",
    )
    from yosai_intel_dashboard.src.services.auth import verify_jwt_token

    assert verify_jwt_token(token)["iss"] == "gateway"
    headers = {"Authorization": f"Bearer {token}"}

    transport = httpx.ASGITransport(app=module.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/analytics/dashboard-summary", headers=headers)

        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

    queries_stub.fetch_dashboard_summary.assert_awaited_once()


@pytest.mark.asyncio
async def test_unauthorized_request(app_factory):
    module, _, _ = app_factory()
    transport = httpx.ASGITransport(app=module.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/analytics/dashboard-summary")
        assert resp.status_code == 401
        assert resp.json() == {
            "detail": {"code": "unauthorized", "message": "unauthorized"}
        }


@pytest.mark.asyncio
async def test_internal_error_response():
    module, queries_stub, _ = load_app()
    from services.auth import verify_jwt_token


    queries_stub.fetch_dashboard_summary.side_effect = RuntimeError("boom")
    token = jwt.encode(
        {"sub": "svc", "iss": "gateway", "exp": int(time.time()) + 60},
        "secret",
        algorithm="HS256",
    )
    assert verify_jwt_token(token)["iss"] == "gateway"
    headers = {"Authorization": f"Bearer {token}"}

    transport = httpx.ASGITransport(app=module.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/api/v1/analytics/dashboard-summary",
            headers=headers,
        )
        assert resp.status_code == 500
        assert resp.json() == {"code": "internal", "message": "boom"}


@pytest.mark.asyncio
async def test_model_registry_endpoints(tmp_path):
    module, _, svc = load_app()
    from services.auth import verify_jwt_token

    svc.model_dir = tmp_path
    from yosai_intel_dashboard.models.ml import ModelRegistry

    svc.model_registry = ModelRegistry()

    token = jwt.encode(
        {"sub": "svc", "iss": "gateway", "exp": int(time.time()) + 60},
        "secret",
        algorithm="HS256",
    )
    from yosai_intel_dashboard.src.services.auth import verify_jwt_token

    assert verify_jwt_token(token)["iss"] == "gateway"
    headers = {"Authorization": f"Bearer {token}"}

    transport = httpx.ASGITransport(app=module.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        files = {"file": ("model.bin", b"data")}
        data = {"name": "demo", "version": "1"}
        resp = await client.post(
            "/api/v1/models/register", headers=headers, data=data, files=files
        )
        assert resp.status_code == 200
        assert resp.json()["version"] == "1"

        resp = await client.get("/api/v1/models/demo", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["versions"] == ["1"]

        resp = await client.post(
            "/api/v1/models/demo/rollback",
            headers=headers,
            data={"version": "1"},
        )
        assert resp.status_code == 200
        assert resp.json()["active_version"] == "1"


@pytest.mark.asyncio
async def test_predict_endpoint(tmp_path):
    module, _, svc = load_app()
    from services.auth import verify_jwt_token

    svc.model_dir = tmp_path

    model = Dummy()
    path = tmp_path / "demo" / "1" / "model.joblib"
    path.parent.mkdir(parents=True)
    joblib.dump(model, path)
    from yosai_intel_dashboard.models.ml import ModelRegistry

    registry = ModelRegistry()
    registry.register_model("demo", str(path), {}, "", version="1")
    registry.set_active_version("demo", "1")
    svc.model_registry = registry
    module.preload_active_models(svc)

    token = jwt.encode(
        {"sub": "svc", "iss": "gateway", "exp": int(time.time()) + 60},
        "secret",
        algorithm="HS256",
    )
    from yosai_intel_dashboard.src.services.auth import verify_jwt_token

    assert verify_jwt_token(token)["iss"] == "gateway"
    headers = {"Authorization": f"Bearer {token}"}

    transport = httpx.ASGITransport(app=module.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/models/demo/predict",
            headers=headers,
            json={"data": [1, 2]},
        )
        assert resp.status_code == 200
        assert resp.json()["predictions"] == [2]


@pytest.mark.asyncio
async def test_batch_predict_endpoint(tmp_path):
    module, _, svc = load_app()
    from services.auth import verify_jwt_token

    svc.model_dir = tmp_path

    model = Dummy()
    svc.models = {"demo": model}

    token = jwt.encode(
        {"sub": "svc", "iss": "gateway", "exp": int(time.time()) + 60},
        "secret",
        algorithm="HS256",
    )
    from yosai_intel_dashboard.src.services.auth import verify_jwt_token

    assert verify_jwt_token(token)["iss"] == "gateway"
    headers = {"Authorization": f"Bearer {token}"}

    csv_content = "col1,col2\n1,2\n3,4\n"

    transport = httpx.ASGITransport(app=module.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        files = {"file": ("data.csv", csv_content)}
        resp = await client.post(
            "/api/v1/analytics/batch_predict",
            headers=headers,
            params={"model": "demo"},
            files=files,
        )
        assert resp.status_code == 200
        assert resp.json()["predictions"] == [2]
