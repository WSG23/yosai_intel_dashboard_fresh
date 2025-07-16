import types
import pytest
from cryptography.fernet import Fernet

from config.secure_config_manager import SecureConfigManager
from core.exceptions import ConfigurationError


def test_vault_secret_resolution(monkeypatch, tmp_path):
    key = Fernet.generate_key()
    f = Fernet(key)
    encrypted = f.encrypt(b"super-secret").decode()

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

    assert mgr.get_database_config().password == "super-secret"
    assert mgr.get_security_config().secret_key == "super-secret"


def test_missing_vault_credentials(monkeypatch):
    monkeypatch.delenv("VAULT_ADDR", raising=False)
    monkeypatch.delenv("VAULT_TOKEN", raising=False)

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
