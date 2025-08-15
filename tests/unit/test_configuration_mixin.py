from types import SimpleNamespace

from yosai_intel_dashboard.src.infrastructure.config.configuration_mixin import ConfigurationMixin


class EmptyConfig(ConfigurationMixin):
    pass


class CustomConfig(ConfigurationMixin):
    def __init__(self) -> None:
        self.performance = SimpleNamespace(ai_confidence_threshold=0.9)
        self.security = SimpleNamespace(max_upload_mb=123)
        self.uploads = SimpleNamespace(DEFAULT_CHUNK_SIZE=456)


def test_defaults():
    cfg = EmptyConfig()
    assert cfg.get_ai_confidence_threshold() == 0.8
    assert cfg.get_max_upload_size_mb() == 50
    assert cfg.get_upload_chunk_size() == 1024


def test_overrides():
    cfg = CustomConfig()
    assert cfg.get_ai_confidence_threshold() == 0.9
    assert cfg.get_max_upload_size_mb() == 123
    assert cfg.get_upload_chunk_size() == 456
