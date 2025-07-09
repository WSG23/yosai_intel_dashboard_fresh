import json
import os

import pytest

from config.config import create_config_manager
from config.dynamic_config import DynamicConfigManager


def test_yaml_and_env_loading(monkeypatch, tmp_path):
    yaml_text = """
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
    monkeypatch.setenv("SECRET_VAR", "secret")
    monkeypatch.setenv("SECRET_KEY", "secret")
    # required env vars
    monkeypatch.setenv("DB_PASSWORD", "pwd")
    monkeypatch.setenv("AUTH0_CLIENT_ID", "cid")
    monkeypatch.setenv("AUTH0_CLIENT_SECRET", "csecret")
    monkeypatch.setenv("AUTH0_DOMAIN", "domain")
    monkeypatch.setenv("AUTH0_AUDIENCE", "aud")

    cfg = create_config_manager()
    assert cfg.get_app_config().title == "Demo \u0394"


def test_json_env_rules_parsed(monkeypatch):
    monkeypatch.setenv("VALIDATOR_RULES", '{"xss": false, "sql_injection": false}')
    dynamic = DynamicConfigManager()
    assert dynamic.uploads.VALIDATOR_RULES["xss"] is False
    assert dynamic.uploads.VALIDATOR_RULES["sql_injection"] is False
