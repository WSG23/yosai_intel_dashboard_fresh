import builtins
import os
import types

import pytest

from yosai_intel_dashboard.src.core.secret_manager import SecretManager, validate_secrets


def test_get_env_secret(monkeypatch):
    value = os.urandom(16).hex()
    monkeypatch.setenv("MY_SECRET", value)
    mgr = SecretManager("env")
    assert mgr.get("MY_SECRET") == value


def test_get_missing_secret_raises(monkeypatch):
    monkeypatch.delenv("MISSING_SECRET", raising=False)
    mgr = SecretManager("env")
    with pytest.raises(KeyError):
        mgr.get("MISSING_SECRET")


def test_generate_and_validate_secret_key(monkeypatch):
    mgr = SecretManager()
    key = mgr.rotate_secret("SECRET_KEY", 32)
    assert mgr.get("SECRET_KEY") == key


def test_validate_secrets_summary(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", os.urandom(32).hex())
    monkeypatch.setenv("AUTH0_CLIENT_ID", "id")
    monkeypatch.setenv("AUTH0_CLIENT_SECRET", os.urandom(16).hex())
    monkeypatch.setenv("AUTH0_DOMAIN", "domain")
    monkeypatch.setenv("AUTH0_AUDIENCE", "aud")
    monkeypatch.setenv("DB_PASSWORD", os.urandom(32).hex())
    summary = validate_secrets()
    assert summary["checks"]["SECRET_KEY"]
    assert summary["valid"]
