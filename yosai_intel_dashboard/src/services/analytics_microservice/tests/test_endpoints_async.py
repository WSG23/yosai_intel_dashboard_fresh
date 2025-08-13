from __future__ import annotations

import httpx
import joblib
import pytest


class Dummy:
    def predict(self, data):
        return [len(data)]


@pytest.mark.asyncio
async def test_health_endpoints(app_factory, client):
    module, _, _ = app_factory()
    async with client(module.app) as http_client:
        resp = await http_client.get("/api/v1/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

        resp = await http_client.get("/api/v1/health/live")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

        resp = await http_client.get("/api/v1/health/startup")
        assert resp.status_code == 200
        assert resp.json() == {"status": "complete"}

        resp = await http_client.get("/api/v1/health/ready")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ready"}


@pytest.mark.asyncio
async def test_dashboard_summary_endpoint(app_factory, token_factory, client):
    module, queries_stub, _ = app_factory()
    token = token_factory()
    headers = {"Authorization": f"Bearer {token}"}

    async with client(module.app) as http_client:
        resp = await http_client.get(
            "/api/v1/analytics/dashboard-summary", headers=headers
        )
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

    queries_stub.fetch_dashboard_summary.assert_awaited_once()


@pytest.mark.asyncio
async def test_unauthorized_request(app_factory, client):
    module, _, _ = app_factory()
    async with client(module.app) as http_client:
        resp = await http_client.get("/api/v1/analytics/dashboard-summary")
        assert resp.status_code == 401
        assert resp.json() == {
            "detail": {"code": "unauthorized", "message": "unauthorized"}
        }


@pytest.mark.asyncio
async def test_internal_error_response(app_factory, token_factory, client):
    module, queries_stub, _ = app_factory()
    queries_stub.fetch_dashboard_summary.side_effect = RuntimeError("boom")
    token = token_factory()
    headers = {"Authorization": f"Bearer {token}"}

    async with client(module.app) as http_client:
        resp = await http_client.get(
            "/api/v1/analytics/dashboard-summary", headers=headers
        )
        assert resp.status_code == 500
        assert resp.json() == {"code": "internal", "message": "boom"}


@pytest.mark.asyncio
async def test_model_registry_endpoints(app_factory, tmp_path, token_factory, client):
    module, _, svc = app_factory()

    svc.model_dir = tmp_path
    from yosai_intel_dashboard.models.ml import ModelRegistry

    svc.model_registry = ModelRegistry()

    token = token_factory()
    headers = {"Authorization": f"Bearer {token}"}

    async with client(module.app) as http_client:
        files = {"file": ("model.bin", b"data")}
        data = {"name": "demo", "version": "1"}
        resp = await http_client.post(
            "/api/v1/models/register", headers=headers, data=data, files=files
        )
        assert resp.status_code == 200
        assert resp.json()["version"] == "1"

        resp = await http_client.get("/api/v1/models/demo", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["versions"] == ["1"]

        resp = await http_client.post(
            "/api/v1/models/demo/rollback",
            headers=headers,
            data={"version": "1"},
        )
        assert resp.status_code == 200
        assert resp.json()["active_version"] == "1"


@pytest.mark.asyncio
async def test_predict_endpoint(app_factory, tmp_path, token_factory, client):
    module, _, svc = app_factory()

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
    from yosai_intel_dashboard.src.services.analytics_microservice.model_loader import (
        preload_active_models,
    )

    preload_active_models(svc)

    token = token_factory()
    headers = {"Authorization": f"Bearer {token}"}

    async with client(module.app) as http_client:
        resp = await http_client.post(
            "/api/v1/models/demo/predict",
            headers=headers,
            json={"data": [1, 2]},
        )
        assert resp.status_code == 200
        assert resp.json()["predictions"] == [2]


@pytest.mark.asyncio
async def test_batch_predict_endpoint(app_factory, tmp_path, token_factory, client):
    module, _, svc = app_factory()

    svc.model_dir = tmp_path

    model = Dummy()
    svc.models = {"demo": model}

    token = token_factory()
    headers = {"Authorization": f"Bearer {token}"}

    csv_content = "col1,col2\n1,2\n3,4\n"

    async with client(module.app) as http_client:
        files = {"file": ("data.csv", csv_content)}
        resp = await http_client.post(
            "/api/v1/analytics/batch_predict",
            headers=headers,
            params={"model": "demo"},
            files=files,
        )
        assert resp.status_code == 200
        assert resp.json()["predictions"] == [2]
