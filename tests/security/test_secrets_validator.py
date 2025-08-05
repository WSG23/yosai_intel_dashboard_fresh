import json

import pytest
from flask import Flask

from yosai_intel_dashboard.src.core.secret_manager import SecretsManager
from yosai_intel_dashboard.src.infrastructure.security.secrets_validator import (
    SecretsValidator,
    register_health_endpoint,
)


class DummyManager(SecretsManager):
    def __init__(self, secret: str):
        super().__init__(docker_dir=".")
        self._secret = secret

    def get(self, key: str, default=None):  # type: ignore[override]
        return self._secret


def _create_app(secret: str, env: str) -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = secret
    app.config["ENV"] = env
    validator = SecretsValidator(DummyManager(secret))
    register_health_endpoint(app, validator)
    return app


def test_production_failure():
    validator = SecretsValidator(DummyManager("dev"))
    result = validator.validate_secret("dev", environment="production")
    assert result["errors"]


def test_staging_warning():
    validator = SecretsValidator(DummyManager("dev"))
    result = validator.validate_secret("dev", environment="staging")
    assert result["warnings"] and not result["errors"]


def test_entropy_check():
    low_entropy = "aaaaaaaaaaaaaa"
    validator = SecretsValidator(DummyManager(low_entropy))
    result = validator.validate_secret(low_entropy, environment="production")
    assert result["entropy"] < SecretsValidator.MIN_ENTROPY
    assert result["errors"]


def test_pattern_matching():
    insecure = "change-me-now"
    validator = SecretsValidator(DummyManager(insecure))
    result = validator.validate_secret(insecure, environment="production")
    assert any(
        "pattern" in e or "pattern" in w for e in result["errors"] + result["warnings"]
    )


def test_health_endpoint():
    app = _create_app("dev", "production")
    client = app.test_client()
    resp = client.get("/health/secrets")
    data = json.loads(resp.data)
    assert resp.status_code == 500
    assert data["errors"]


def test_health_endpoint_warning():
    app = _create_app("dev", "staging")
    client = app.test_client()
    resp = client.get("/health/secrets")
    data = json.loads(resp.data)
    assert resp.status_code == 200
    assert data["warnings"]
