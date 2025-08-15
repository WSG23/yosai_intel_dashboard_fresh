import os

from yosai_intel_dashboard.src.infrastructure.config import create_config_manager


def test_environment_overrides(monkeypatch):
    monkeypatch.setenv("DB_HOST", "db.example.com")
    monkeypatch.setenv("DB_PORT", "1234")
    # required vars
    monkeypatch.setenv("SECRET_KEY", "s")
    monkeypatch.setenv("DB_PASSWORD", "pwd")
    monkeypatch.setenv("AUTH0_CLIENT_ID", "cid")
    monkeypatch.setenv("AUTH0_CLIENT_SECRET", "secret")
    monkeypatch.setenv("AUTH0_DOMAIN", "dom")
    monkeypatch.setenv("AUTH0_AUDIENCE", "aud")

    cfg = create_config_manager()
    db = cfg.get_database_config()
    assert db.host == "db.example.com"
    assert db.port == 1234
