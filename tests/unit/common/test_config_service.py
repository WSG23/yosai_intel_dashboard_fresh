from __future__ import annotations

import pytest

from src.common.config import ConfigService


def test_load_defaults(monkeypatch):
    monkeypatch.setenv("METRICS_INTERVAL", "1")
    monkeypatch.setenv("PING_INTERVAL", "2")
    monkeypatch.setenv("PING_TIMEOUT", "3")
    cfg = ConfigService()
    assert cfg.metrics_interval == 1.0
    assert cfg.ping_interval == 2.0
    assert cfg.ping_timeout == 3.0


def test_custom_mapping_immutable():
    cfg = ConfigService(
        {"metrics_interval": 0.1, "ping_interval": 0.2, "ping_timeout": 0.3}
    )
    with pytest.raises(TypeError):
        cfg._settings["metrics_interval"] = 2
