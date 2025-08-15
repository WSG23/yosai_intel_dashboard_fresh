from __future__ import annotations

from types import SimpleNamespace

from yosai_intel_dashboard.src.infrastructure.config.configuration_mixin import (
    ConfigurationMixin,
)


class DummyConfig(ConfigurationMixin):
    pass


# AI confidence threshold ------------------------------------------------------


def test_ai_confidence_threshold_default():
    assert DummyConfig().get_ai_confidence_threshold() == 0.8


def test_ai_confidence_threshold_performance():
    cfg = DummyConfig()
    cfg.performance = SimpleNamespace(ai_confidence_threshold=0.9)
    assert cfg.get_ai_confidence_threshold() == 0.9


def test_ai_confidence_threshold_direct():
    cfg = DummyConfig()
    cfg.ai_confidence_threshold = 0.91
    assert cfg.get_ai_confidence_threshold() == 0.91


def test_ai_confidence_threshold_alt_name():
    cfg = DummyConfig()
    cfg.ai_threshold = 0.77
    assert cfg.get_ai_confidence_threshold() == 0.77


# Maximum upload size ----------------------------------------------------------


def test_max_upload_size_default():
    assert DummyConfig().get_max_upload_size_mb() == 50


def test_max_upload_size_security():
    cfg = DummyConfig()
    cfg.security = SimpleNamespace(max_upload_mb=100)
    assert cfg.get_max_upload_size_mb() == 100


def test_max_upload_size_direct():
    cfg = DummyConfig()
    cfg.max_upload_size_mb = 66
    assert cfg.get_max_upload_size_mb() == 66


def test_max_upload_size_alt_name():
    cfg = DummyConfig()
    cfg.max_size_mb = 70
    assert cfg.get_max_upload_size_mb() == 70


def test_max_upload_size_upload_attr():
    cfg = DummyConfig()
    cfg.upload = SimpleNamespace(max_file_size_mb=80)
    assert cfg.get_max_upload_size_mb() == 80


# Upload chunk size ------------------------------------------------------------


def test_upload_chunk_size_default():
    assert DummyConfig().get_upload_chunk_size() == 1024


def test_upload_chunk_size_uploads():
    cfg = DummyConfig()
    cfg.uploads = SimpleNamespace(DEFAULT_CHUNK_SIZE=2048)
    assert cfg.get_upload_chunk_size() == 2048


def test_upload_chunk_size_direct():
    cfg = DummyConfig()
    cfg.upload_chunk_size = 256
    assert cfg.get_upload_chunk_size() == 256


def test_upload_chunk_size_alt_name():
    cfg = DummyConfig()
    cfg.chunk_size = 128
    assert cfg.get_upload_chunk_size() == 128
