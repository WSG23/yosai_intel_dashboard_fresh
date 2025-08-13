from __future__ import annotations

import os

import pytest

from yosai_intel_dashboard.src.infrastructure.config.secrets_validator import (
    SecretSource,
    SecretsValidator,
)
from yosai_intel_dashboard.src.infrastructure.config.secure_config_manager import (
    SecureConfigManager,
)


class MappingSource(SecretSource):
    def __init__(self, mapping):
        self.mapping = mapping

    def get_secret(self, key: str):
        return self.mapping.get(key)


def test_resolves_vault_reference(monkeypatch):
    def fake_read_vault(self, path, field):
        assert path == "secret/path"
        assert field == "token"
        return "v" * 32

    monkeypatch.setattr(SecureConfigManager, "_read_vault_secret", fake_read_vault)

    src = MappingSource(
        {
            "SECRET_KEY": "vault:secret/path#token",
            "DB_PASSWORD": os.urandom(32).hex(),
            "AUTH0_CLIENT_SECRET": os.urandom(32).hex(),
        }
    )

    validator = SecretsValidator(environment="production")
    secrets = validator.validate_production_secrets(src)
    assert secrets["SECRET_KEY"] == "v" * 32


def test_resolves_aws_reference(monkeypatch):
    def fake_read_aws(self, name):
        assert name == "db/pass"
        return "a" * 32

    monkeypatch.setattr(SecureConfigManager, "_read_aws_secret", fake_read_aws)

    src = MappingSource(
        {
            "SECRET_KEY": os.urandom(32).hex(),
            "DB_PASSWORD": "aws-secrets:db/pass",
            "AUTH0_CLIENT_SECRET": os.urandom(32).hex(),
        }
    )

    validator = SecretsValidator(environment="production")
    secrets = validator.validate_production_secrets(src)
    assert secrets["DB_PASSWORD"] == "a" * 32


def test_resolves_file_reference(tmp_path):
    secret_path = tmp_path / "secret"
    secret_path.write_text("f" * 32, encoding="utf-8")

    src = MappingSource(
        {
            "SECRET_KEY": f"file:{secret_path}",
            "DB_PASSWORD": os.urandom(32).hex(),
            "AUTH0_CLIENT_SECRET": os.urandom(32).hex(),
        }
    )

    validator = SecretsValidator(environment="production")
    secrets = validator.validate_production_secrets(src)
    assert secrets["SECRET_KEY"] == "f" * 32
