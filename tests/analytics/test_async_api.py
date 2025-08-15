import json

from fastapi.testclient import TestClient

from yosai_intel_dashboard.src.services.analytics.async_api import app
from yosai_intel_dashboard.src.infrastructure.callbacks import (
    CallbackType,
    trigger_callback,
)


def test_health_endpoint():
    with TestClient(app) as client:
        resp = client.get("/api/v1/analytics/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"


def test_chart_bad_type():
    with TestClient(app) as client:
        resp = client.get("/api/v1/analytics/chart/bad")
        assert resp.status_code == 400


def test_websocket_updates():
    with TestClient(app) as client:
        with client.websocket_connect("/api/v1/ws/analytics") as ws:
            trigger_callback(CallbackType.ANALYTICS_UPDATE, {"a": 1})
            data = ws.receive_text()
            assert json.loads(data)["a"] == 1


def test_generate_report_json(monkeypatch):
    class DummySvc:
        def generate_report(self, report_type, params):
            return {"report_type": report_type, "params": params}

    import yosai_intel_dashboard.src.services.analytics.async_api as mod

    monkeypatch.setattr(mod, "get_analytics_service", lambda: DummySvc())
    with TestClient(app) as client:
        resp = client.post(
            "/api/v1/analytics/report",
            json={"type": "summary", "timeframe": "7d"},
        )
        assert resp.status_code == 200
        assert resp.json() == {
            "report_type": "summary",
            "params": {"timeframe": "7d"},
        }


def test_generate_report_file(monkeypatch):
    class DummySvc:
        def generate_report(self, report_type, params):
            return {"report_type": report_type}

    import yosai_intel_dashboard.src.services.analytics.async_api as mod

    monkeypatch.setattr(mod, "get_analytics_service", lambda: DummySvc())
    with TestClient(app) as client:
        resp = client.post(
            "/api/v1/analytics/report",
            json={"type": "summary", "format": "file"},
        )
        assert resp.status_code == 200
        assert resp.headers["content-disposition"].startswith("attachment")
