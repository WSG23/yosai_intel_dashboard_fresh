import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from yosai_intel_dashboard.src.adapters.api.model_router import create_model_router
from yosai_intel_dashboard.src.services.model_service import ModelService


def _setup_app(tmp_path: Path) -> TestClient:
    registry = {
        "demo": {
            "versions": {
                "1": {"factor": 1.0},
                "2": {"factor": 2.0},
            },
            "active": "1",
            "rollout": {"1": 1.0},
        }
    }
    reg_path = tmp_path / "registry.json"
    reg_path.write_text(json.dumps(registry))
    service = ModelService(registry_path=reg_path)
    app = FastAPI()
    app.include_router(create_model_router(service))
    return TestClient(app)


def test_versioned_prediction(tmp_path: Path) -> None:
    client = _setup_app(tmp_path)
    resp = client.post("/models/demo/v2/predict", json={"value": 3})
    assert resp.status_code == 200
    data = resp.json()
    assert data["version"] == "2"
    assert data["result"] == 6


def test_ab_rollout_switch(tmp_path: Path) -> None:
    client = _setup_app(tmp_path)
    resp = client.post("/models/demo/predict", json={"value": 4})
    assert resp.json()["version"] == "1"
    resp = client.post("/models/demo/rollout", json={"rollout": {"2": 1.0}})
    assert resp.status_code == 200
    resp = client.post("/models/demo/predict", json={"value": 4})
    assert resp.json()["version"] == "2"
    assert resp.json()["result"] == 8
