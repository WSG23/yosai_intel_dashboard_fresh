import json
import os

import pytest

from config import create_config_manager
from yosai_intel_dashboard.src.infrastructure.config.dynamic_config import DynamicConfigManager


def test_yaml_and_env_loading(monkeypatch, tmp_path):
    secret = os.urandom(16).hex()
    yaml_text = f"""
app:
  title: "Demo ${APP_EXTRA}"
database:
  name: demo.db
security:
  secret_key: ${SECRET_VAR}
"""
    path = tmp_path / "config.yaml"
    path.write_text(yaml_text, encoding="utf-8")

    monkeypatch.setenv("YOSAI_CONFIG_FILE", str(path))
    monkeypatch.setenv("APP_EXTRA", "\u0394")
    monkeypatch.setenv("SECRET_VAR", secret)
    monkeypatch.setenv("SECRET_KEY", secret)
    # required env vars
    monkeypatch.setenv(
        "DB_PASSWORD", os.environ.get("DB_PASSWORD", os.urandom(16).hex())
    )
    monkeypatch.setenv("AUTH0_CLIENT_ID", "cid")
    monkeypatch.setenv(
        "AUTH0_CLIENT_SECRET",
        os.environ.get("AUTH0_CLIENT_SECRET", os.urandom(16).hex()),
    )
    monkeypatch.setenv("AUTH0_DOMAIN", "domain")
    monkeypatch.setenv("AUTH0_AUDIENCE", "aud")

    cfg = create_config_manager()
    assert cfg.get_app_config().title == "Demo \u0394"


def test_json_env_rules_parsed(monkeypatch):
    monkeypatch.setenv("VALIDATOR_RULES", '{"xss": false, "sql_injection": false}')
    dynamic = DynamicConfigManager()
    assert dynamic.uploads.VALIDATOR_RULES["xss"] is False
    assert dynamic.uploads.VALIDATOR_RULES["sql_injection"] is False


def test_env_overrides_applied(monkeypatch):
    monkeypatch.setenv("YOSAI_DATABASE_HOST", "db.example.com")
    monkeypatch.setenv("YOSAI_DATABASE_PORT", "1234")
    secret = os.urandom(16).hex()
    monkeypatch.setenv("SECRET_KEY", secret)
    monkeypatch.setenv("YOSAI_SECURITY_SECRET_KEY", secret)
    monkeypatch.setenv("YOSAI_DATABASE_PASSWORD", os.urandom(16).hex())
    monkeypatch.setenv("AUTH0_CLIENT_ID", "cid")
    monkeypatch.setenv("AUTH0_CLIENT_SECRET", os.urandom(16).hex())
    monkeypatch.setenv("AUTH0_DOMAIN", "dom")
    monkeypatch.setenv("AUTH0_AUDIENCE", "aud")

    cfg = create_config_manager()
    db = cfg.get_database_config()
    assert db.host == "db.example.com"
    assert db.port == 1234


def test_password_from_env(monkeypatch, tmp_path):
    yaml_text = """
app: {}
database:
  user: demo
security: {}
"""
    path = tmp_path / "cfg.yaml"
    path.write_text(yaml_text, encoding="utf-8")

    monkeypatch.setenv("YOSAI_CONFIG_FILE", str(path))
    secret = os.urandom(16).hex()
    monkeypatch.setenv("SECRET_KEY", secret)
    monkeypatch.setenv("YOSAI_SECURITY_SECRET_KEY", secret)
    monkeypatch.setenv("YOSAI_DATABASE_PASSWORD", os.urandom(16).hex())
    monkeypatch.setenv("AUTH0_CLIENT_ID", "cid")
    monkeypatch.setenv("AUTH0_CLIENT_SECRET", os.urandom(16).hex())
    monkeypatch.setenv("AUTH0_DOMAIN", "domain")
    monkeypatch.setenv("AUTH0_AUDIENCE", "aud")

    cfg = create_config_manager()
    assert cfg.get_database_config().password == "envpass"
