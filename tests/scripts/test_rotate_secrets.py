"""Tests for scripts.rotate_secrets."""

from __future__ import annotations

import types

import yaml

from scripts import rotate_secrets


class DummyVault:
    def __init__(self) -> None:
        self.stored = {}
        self.secrets = types.SimpleNamespace(kv=types.SimpleNamespace(v2=self))

    def create_or_update_secret(self, path: str, secret: dict) -> None:  # type: ignore[override]
        self.stored[path] = secret


class DummyAWS:
    class exceptions:  # pragma: no cover - simple namespace
        class ResourceNotFoundException(Exception):
            pass

    def __init__(self) -> None:
        self.values = {}

    def put_secret_value(self, SecretId: str, SecretString: str) -> None:
        self.values[SecretId] = SecretString

    def create_secret(
        self, Name: str, SecretString: str
    ) -> None:  # pragma: no cover - not used
        self.values[Name] = SecretString


def test_update_secrets_vault(monkeypatch, tmp_path):
    path = tmp_path / "secrets.yaml"
    path.write_text("stringData: {}\n", encoding="utf-8")

    client = DummyVault()
    monkeypatch.setattr(rotate_secrets, "_get_vault_client", lambda: client)
    monkeypatch.setattr(rotate_secrets, "_get_aws_client", lambda: None)

    refs = rotate_secrets.update_secrets(file_path=path)

    data = yaml.safe_load(path.read_text())
    assert data["stringData"]["SECRET_KEY"].startswith("vault:")
    assert client.stored  # ensure something was written
    assert all(r.startswith("vault:") for r in refs.values())


def test_update_secrets_aws(monkeypatch, tmp_path):
    path = tmp_path / "secrets.yaml"
    path.write_text("stringData: {}\n", encoding="utf-8")

    client = DummyAWS()
    monkeypatch.setattr(rotate_secrets, "_get_vault_client", lambda: None)
    monkeypatch.setattr(rotate_secrets, "_get_aws_client", lambda: client)

    refs = rotate_secrets.update_secrets(file_path=path)

    data = yaml.safe_load(path.read_text())
    assert data["stringData"]["SECRET_KEY"].startswith("aws-secrets:")
    assert client.values  # ensure something was written
    assert all(r.startswith("aws-secrets:") for r in refs.values())
