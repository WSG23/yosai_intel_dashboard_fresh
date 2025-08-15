from fastapi.testclient import TestClient

from services.api.main import app


client = TestClient(app)


def test_not_found_returns_error_response():
    resp = client.get("/does-not-exist")
    assert resp.status_code == 404
    assert resp.json()["code"] == "not_found"


def test_validation_error_returns_error_response():
    resp = client.post("/api/v1/echo", json={})
    assert resp.status_code == 400
    body = resp.json()
    assert body["code"] == "invalid_input"
    assert body["message"] == "Invalid input"
