import builtins
import os
import types

import pytest

from core.secret_manager import SecretManager, validate_secrets


def test_get_env_secret(monkeypatch):
    monkeypatch.setenv("MY_SECRET", "value")
    mgr = SecretManager("env")
    assert mgr.get("MY_SECRET") == "value"


def test_get_missing_secret_raises(monkeypatch):
    monkeypatch.delenv("MISSING_SECRET", raising=False)
    mgr = SecretManager("env")
    with pytest.raises(KeyError):
        mgr.get("MISSING_SECRET")


def test_generate_and_validate_secret_key(monkeypatch):
    key = SecretManager.generate_secret_key(32)
    monkeypatch.setenv("SECRET_KEY", key)
    assert SecretManager.get_secret_key() == key


def test_validate_secrets_summary(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "s" * 32)
    monkeypatch.setenv("AUTH0_CLIENT_ID", "id")
    monkeypatch.setenv("AUTH0_CLIENT_SECRET", "secret")
    monkeypatch.setenv("AUTH0_DOMAIN", "domain")
    monkeypatch.setenv("AUTH0_AUDIENCE", "aud")
    monkeypatch.setenv("DB_PASSWORD", "p" * 32)
    summary = validate_secrets()
    assert summary["checks"]["SECRET_KEY"]
    assert summary["valid"]
