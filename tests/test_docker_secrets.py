from __future__ import annotations

import os
from pathlib import Path

import pytest

from yosai_intel_dashboard.src.infrastructure.config.secrets_validator import (
    DockerSecretSource,
    SecretsValidator,
)


def test_docker_secret_source(tmp_path):
    # placeholder value used for test secrets
    secret_value = "placeholdersecret" * 2
    (tmp_path / "SECRET_KEY").write_text(secret_value)
    src = DockerSecretSource(tmp_path)
    assert src.get_secret("SECRET_KEY") == secret_value

    assert src.get_secret("MISSING") is None


def test_validate_production_secrets_with_docker(tmp_path):
    (tmp_path / "SECRET_KEY").write_text("k" * 32)
    (tmp_path / "DB_PASSWORD").write_text("p" * 32)
    (tmp_path / "AUTH0_CLIENT_SECRET").write_text("s" * 32)
    src = DockerSecretSource(tmp_path)
    validator = SecretsValidator(environment="production")
    secrets = validator.validate_production_secrets(src)
    assert secrets["SECRET_KEY"] == "kkkk" + "*" * 24 + "kkkk"
    assert secrets["DB_PASSWORD"] == "pppp" + "*" * 24 + "pppp"
    assert secrets["AUTH0_CLIENT_SECRET"] == "ssss" + "*" * 24 + "ssss"


def test_validate_production_secrets_mask_toggle(tmp_path):
    (tmp_path / "SECRET_KEY").write_text("k" * 32)
    (tmp_path / "DB_PASSWORD").write_text("p" * 32)
    (tmp_path / "AUTH0_CLIENT_SECRET").write_text("s" * 32)
    src = DockerSecretSource(tmp_path)
    validator = SecretsValidator(environment="production")

    masked = validator.validate_production_secrets(src)
    assert masked["SECRET_KEY"].startswith("kkkk")
    assert "*" in masked["SECRET_KEY"]

    unmasked = validator.validate_production_secrets(src, mask=False)
    assert unmasked["SECRET_KEY"] == "k" * 32
    assert unmasked["AUTH0_CLIENT_SECRET"] == "s" * 32
