import os

import pytest

from yosai_intel_dashboard.src.infrastructure.config import dev_mode


def test_dev_mode_requires_secrets(monkeypatch, caplog):
    monkeypatch.setenv("YOSAI_ENV", "development")
    for var in [
        "AUTH0_CLIENT_ID",
        "AUTH0_CLIENT_SECRET",
        "AUTH0_DOMAIN",
        "AUTH0_AUDIENCE",
        "SECRET_KEY",
        "DB_PASSWORD",
    ]:
        monkeypatch.delenv(var, raising=False)

    with caplog.at_level("WARNING"):
        dev_mode.setup_dev_mode()

    assert any(
        "Missing environment variables" in r.getMessage() for r in caplog.records
    )


def test_dev_mode_warning_contains_instruction(monkeypatch, caplog):
    monkeypatch.setenv("YOSAI_ENV", "development")
    monkeypatch.setenv("AUTH0_CLIENT_ID", "1")
    monkeypatch.setenv("AUTH0_CLIENT_SECRET", "1")
    monkeypatch.setenv("AUTH0_DOMAIN", "1")
    monkeypatch.setenv("AUTH0_AUDIENCE", "1")
    monkeypatch.setenv("SECRET_KEY", "1")
    monkeypatch.delenv("DB_PASSWORD", raising=False)

    with caplog.at_level("WARNING"):
        dev_mode.setup_dev_mode()

    assert any("cp .env.example .env" in r.getMessage() for r in caplog.records)
