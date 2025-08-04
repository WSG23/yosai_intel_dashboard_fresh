from __future__ import annotations

import os
import types

import pytest
from cryptography.fernet import Fernet

from yosai_intel_dashboard.src.core.exceptions import ConfigurationError
from yosai_intel_dashboard.src.infrastructure.config.secure_config_manager import (
    SecureConfigManager,
)

pytest.importorskip("cryptography")


def test_vault_secret_resolution(monkeypatch, tmp_path):
    key = Fernet.generate_key()
    f = Fernet(key)
    secret = os.urandom(16).hex()
    encrypted = f.encrypt(secret.encode()).decode()

    class DummyKV:
        def read_secret_version(self, path):
            assert path == "secret/data/db"
            return {"data": {"data": {"password": encrypted}}}

    class DummyClient:
        def __init__(self, url=None, token=None):  # noqa: D401 - stub
            self.secrets = types.SimpleNamespace(kv=types.SimpleNamespace(v2=DummyKV()))

    monkeypatch.setattr("config.secure_config_manager.hvac.Client", DummyClient)

    cfg_yaml = """
app:
  title: Test
database:
  password: vault:secret/data/db#password
security:
  secret_key: vault:secret/data/db#password
"""
    path = tmp_path / "cfg.yaml"
    path.write_text(cfg_yaml, encoding="utf-8")

    monkeypatch.setenv("YOSAI_CONFIG_FILE", str(path))
    monkeypatch.setenv("FERNET_KEY", key.decode())
    monkeypatch.setenv("VAULT_ADDR", "http://vault")
    monkeypatch.setenv("VAULT_TOKEN", "token")
    monkeypatch.delenv("DB_PASSWORD", raising=False)

    mgr = SecureConfigManager()

    assert mgr.get_database_config().password == secret
    assert mgr.get_security_config().secret_key == secret


def test_missing_vault_credentials(monkeypatch, tmp_path):
    monkeypatch.delenv("VAULT_ADDR", raising=False)
    monkeypatch.delenv("VAULT_TOKEN", raising=False)

    cfg_yaml = """
app:
  title: Test
database:
  password: vault:secret/data/db#password
"""
    path = tmp_path / "cfg.yaml"
    path.write_text(cfg_yaml, encoding="utf-8")

    monkeypatch.setenv("YOSAI_CONFIG_FILE", str(path))

    with pytest.raises(ConfigurationError):
        SecureConfigManager()


def test_secret_retrieval_failure(monkeypatch, tmp_path):
    class DummyKV:
        def read_secret_version(self, path):
            raise RuntimeError("fail")

    class DummyClient:
        def __init__(self, url=None, token=None):  # noqa: D401 - stub
            self.secrets = types.SimpleNamespace(kv=types.SimpleNamespace(v2=DummyKV()))

    monkeypatch.setattr("config.secure_config_manager.hvac.Client", DummyClient)

    cfg_yaml = """
app:
  title: Test
database:
  password: vault:secret/data/db#password
"""
    path = tmp_path / "cfg.yaml"
    path.write_text(cfg_yaml, encoding="utf-8")

    monkeypatch.setenv("YOSAI_CONFIG_FILE", str(path))
    monkeypatch.setenv("VAULT_ADDR", "http://vault")
    monkeypatch.setenv("VAULT_TOKEN", "token")
    monkeypatch.delenv("DB_PASSWORD", raising=False)

    with pytest.raises(ConfigurationError):
        SecureConfigManager()


def test_aws_secret_resolution(monkeypatch, tmp_path):
    aws_secret = os.urandom(16).hex()

    class DummyAWS:
        def __init__(self, region_name=None):  # noqa: D401 - stub
            pass

        def get_secret_value(self, SecretId):
            assert SecretId == "prod/db_password"
            return {"SecretString": aws_secret}

    monkeypatch.setattr(
        "config.secure_config_manager.boto3.client", lambda *a, **k: DummyAWS()
    )
    monkeypatch.setattr(
        "config.secure_config_manager.hvac.Client", lambda *a, **k: None
    )

    cfg_yaml = """
app:
  title: Test
database:
  password: aws-secrets:prod/db_password
security:
  secret_key: dummy
"""
    path = tmp_path / "cfg.yaml"
    path.write_text(cfg_yaml, encoding="utf-8")

    monkeypatch.setenv("YOSAI_CONFIG_FILE", str(path))
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.delenv("DB_PASSWORD", raising=False)

    mgr = SecureConfigManager()

    assert mgr.get_database_config().password == aws_secret
