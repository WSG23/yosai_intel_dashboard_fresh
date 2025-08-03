import os
from pathlib import Path

import pytest

from yosai_intel_dashboard.src.infrastructure.config.secrets_validator import DockerSecretSource, SecretsValidator


def test_docker_secret_source(tmp_path):
    # placeholder value used for test secrets
    (tmp_path / "SECRET_KEY").write_text("placeholdersecret" * 2)
    src = DockerSecretSource(tmp_path)
    # the source should read back the exact secret written to disk
    assert src.get_secret("SECRET_KEY").startswith("placeholdersecret")
    assert src.get_secret("MISSING") is None


def test_validate_production_secrets_with_docker(tmp_path):
    (tmp_path / "SECRET_KEY").write_text("k" * 32)
    (tmp_path / "DB_PASSWORD").write_text("p" * 32)
    (tmp_path / "AUTH0_CLIENT_SECRET").write_text("s" * 32)
    src = DockerSecretSource(tmp_path)
    validator = SecretsValidator(environment="production")
    secrets = validator.validate_production_secrets(src)
    assert secrets["SECRET_KEY"].startswith("k")
    assert secrets["DB_PASSWORD"].startswith("p")


def test_validate_secret_returns_generated_secret():
    """An insecure development secret should be replaced and returned."""
    validator = SecretsValidator(environment="development")
    result, generated = validator.validate_secret("dev")
    assert result.is_valid
    assert generated is not None
    assert len(generated) == 32
