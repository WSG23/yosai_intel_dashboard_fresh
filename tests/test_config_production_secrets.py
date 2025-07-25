import pytest

from yosai_intel_dashboard.src.infrastructure.config import create_config_manager

REQUIRED_AUTH_VARS = [
    "AUTH0_CLIENT_ID",
    "AUTH0_CLIENT_SECRET",
    "AUTH0_DOMAIN",
    "AUTH0_AUDIENCE",
]


def set_env(monkeypatch, secret: str) -> None:
    monkeypatch.setenv("YOSAI_ENV", "production")
    monkeypatch.setenv("SECRET_KEY", secret)
    monkeypatch.setenv("DB_PASSWORD", secret)
    for var in REQUIRED_AUTH_VARS:
        monkeypatch.setenv(var, "value")


def test_invalid_secrets_raise(monkeypatch):
    set_env(monkeypatch, "change-me")
    with pytest.raises(ValueError):
        create_config_manager()
