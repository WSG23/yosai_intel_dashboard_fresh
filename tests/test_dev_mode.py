import os

import pytest

from config import dev_mode


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
