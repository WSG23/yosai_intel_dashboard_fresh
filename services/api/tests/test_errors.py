from fastapi.testclient import TestClient

from services.api.main import app


client = TestClient(app)


def test_not_found_returns_error_response() -> None:
    resp = client.get("/does-not-exist")
    assert resp.status_code == 404  # nosec B101
    assert resp.json()["code"] == "not_found"  # nosec B101


def test_validation_error_returns_error_response() -> None:
    resp = client.post("/api/v1/echo", json={}, headers={"X-Roles": "admin"})
    assert resp.status_code == 400  # nosec B101
    body = resp.json()
    assert body["code"] == "invalid_input"  # nosec B101
    assert body["message"] == "Invalid input"  # nosec B101
