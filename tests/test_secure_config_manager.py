import types

from cryptography.fernet import Fernet

from config.secure_config_manager import SecureConfigManager


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
database:
  password: vault:secret/data/db#password
security:
  secret_key: vault:secret/data/db#password
"""
    path = tmp_path / "cfg.yaml"
    path.write_text(cfg_yaml, encoding="utf-8")

    monkeypatch.setenv("YOSAI_CONFIG_FILE", str(path))
    monkeypatch.setenv("FERNET_KEY", key.decode())

    mgr = SecureConfigManager()

    assert mgr.get_database_config().password == "super-secret"
    assert mgr.get_security_config().secret_key == "super-secret"
