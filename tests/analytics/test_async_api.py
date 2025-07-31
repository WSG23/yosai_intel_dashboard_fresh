import json

from fastapi.testclient import TestClient

from yosai_intel_dashboard.src.services.analytics.async_api import app, event_bus


def test_health_endpoint():
    client = TestClient(app)
    resp = client.get("/v1/analytics/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


def test_chart_bad_type():
    client = TestClient(app)
    resp = client.get("/v1/analytics/chart/bad")
    assert resp.status_code == 400


def test_websocket_updates():
    client = TestClient(app)
    with client.websocket_connect("/ws/analytics") as ws:
        event_bus.publish("analytics_update", {"a": 1})
        data = ws.receive_text()
        assert json.loads(data)["a"] == 1


def test_generate_report_json(monkeypatch):
    class DummySvc:
        def generate_report(self, report_type, params):
            return {"report_type": report_type, "params": params}

    import services.analytics.async_api as mod

    monkeypatch.setattr(mod, "get_analytics_service", lambda: DummySvc())
    client = TestClient(app)
    resp = client.post(
        "/v1/analytics/report",
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

    import services.analytics.async_api as mod

    monkeypatch.setattr(mod, "get_analytics_service", lambda: DummySvc())
    client = TestClient(app)
    resp = client.post(
        "/v1/analytics/report",
        json={"type": "summary", "format": "file"},
    )
    assert resp.status_code == 200
    assert resp.headers["content-disposition"].startswith("attachment")
