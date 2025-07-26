import json
from fastapi.testclient import TestClient

from services.analytics.async_api import app, event_bus


def test_health_endpoint():
    client = TestClient(app)
    resp = client.get("/api/v1/analytics/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


def test_chart_bad_type():
    client = TestClient(app)
    resp = client.get("/api/v1/analytics/chart/bad")
    assert resp.status_code == 400


def test_websocket_updates():
    client = TestClient(app)
    with client.websocket_connect("/ws/analytics") as ws:
        event_bus.publish("analytics_update", {"a": 1})
        data = ws.receive_text()
        assert json.loads(data)["a"] == 1
