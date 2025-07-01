import os
from core.app_factory import create_app


def test_secrets_health_endpoint(monkeypatch):
    monkeypatch.setenv("YOSAI_ENV", "development")
    monkeypatch.setenv("SECRET_KEY", "testkey")
    app = create_app(mode="simple")
    server = app.server
    rules = [r.rule for r in server.url_map.iter_rules()]
    assert "/health/secrets" in rules

    client = server.test_client()
    res = client.get("/health/secrets")
    assert res.status_code == 200
    data = res.get_json()
    assert data["checks"]["SECRET_KEY"] is True
    assert data["valid"] is True
