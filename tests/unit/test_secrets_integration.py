import os

from yosai_intel_dashboard.src.core.secret_manager import SecretsManager


def test_env_overrides_docker(tmp_path, monkeypatch):
    secret_file = tmp_path / "SECRET_KEY"
    secret_file.write_text(os.urandom(16).hex())
    monkeypatch.setenv("SECRET_KEY", os.urandom(16).hex())

    manager = SecretsManager(docker_dir=tmp_path)
    assert manager.get("SECRET_KEY") == "env-secret"


def test_docker_fallback(tmp_path, monkeypatch):
    secret_file = tmp_path / "DB_PASSWORD"
    secret_file.write_text(os.urandom(16).hex())
    monkeypatch.delenv("DB_PASSWORD", raising=False)

    manager = SecretsManager(docker_dir=tmp_path)
    assert manager.get("DB_PASSWORD") == "file-pass"
