from __future__ import annotations

from types import SimpleNamespace
import sys
import types

import pytest

from src.common.config import ConfigurationMixin, ConfigService, get_settings


@pytest.mark.parametrize(
    "cfg, expected",
    [
        (SimpleNamespace(ai_confidence_threshold=0.9), 0.9),
        (SimpleNamespace(ai_threshold=0.7), 0.7),
        (SimpleNamespace(performance={"ai_confidence_threshold": 0.5}), 0.5),
        (SimpleNamespace(), 0.8),
    ],
)
def test_get_ai_confidence_threshold(cfg, expected):
    mixin = ConfigurationMixin()
    assert mixin.get_ai_confidence_threshold(cfg) == expected


@pytest.mark.parametrize(
    "cfg, expected",
    [
        (SimpleNamespace(max_upload_size_mb=10), 10),
        (SimpleNamespace(max_upload_mb=11), 11),
        (SimpleNamespace(security={"max_upload_mb": 12}), 12),
        (SimpleNamespace(upload={"max_file_size_mb": 13}), 13),
        (SimpleNamespace(), 50),
    ],
)
def test_get_max_upload_size_mb(cfg, expected):
    mixin = ConfigurationMixin()
    assert mixin.get_max_upload_size_mb(cfg) == expected


@pytest.mark.parametrize(
    "cfg, expected",
    [
        ({"upload_chunk_size": 100}, 100),
        ({"chunk_size": 101}, 101),
        (SimpleNamespace(uploads=SimpleNamespace(DEFAULT_CHUNK_SIZE=102)), 102),
        ({}, 1024),
    ],
)
def test_get_upload_chunk_size(cfg, expected):
    mixin = ConfigurationMixin()
    assert mixin.get_upload_chunk_size(cfg) == expected


def test_get_settings_infra_config(monkeypatch):
    class FakeCfg:
        def get_ai_confidence_threshold(self):
            return 0.6

        def get_max_upload_size_mb(self):
            return 70

        def get_upload_chunk_size(self):
            return 80

    class FakeMonitoring:
        metrics_interval_seconds = 1.5
        health_check_interval = 40
        health_check_timeout = 20

    fake_module = types.SimpleNamespace(
        get_config=lambda: FakeCfg(),
        get_monitoring_config=lambda: FakeMonitoring(),
    )

    monkeypatch.setitem(sys.modules, "yosai_intel_dashboard.src.infrastructure.config", fake_module)

    settings = get_settings()
    assert settings["metrics_interval"] == 1.5
    assert settings["ping_interval"] == 40
    assert settings["ping_timeout"] == 20
    assert settings["ai_confidence_threshold"] == 0.6
    assert settings["max_upload_size_mb"] == 70
    assert settings["upload_chunk_size"] == 80

    cfg = ConfigService()
    assert cfg.metrics_interval == 1.5
    assert cfg.ping_interval == 40
    assert cfg.ping_timeout == 20

