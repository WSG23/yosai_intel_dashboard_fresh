from types import SimpleNamespace
import importlib.util
import sys
from pathlib import Path

# Dynamically import the helpers module under its package name for coverage
helpers_path = (
    Path(__file__).resolve().parents[1]
    / "yosai_intel_dashboard"
    / "src"
    / "core"
    / "utils"
    / "config_helpers.py"
)
module_name = "yosai_intel_dashboard.src.core.utils.config_helpers"
_spec = importlib.util.spec_from_file_location(module_name, helpers_path)
config_helpers = importlib.util.module_from_spec(_spec)
sys.modules[module_name] = config_helpers
_spec.loader.exec_module(config_helpers)  # type: ignore


class Dummy:
    def __init__(self):
        self.performance = SimpleNamespace(ai_confidence_threshold=0.9)
        self.upload = SimpleNamespace(max_file_size_mb=42)
        self.uploads = SimpleNamespace(DEFAULT_CHUNK_SIZE=256)
        self.security = SimpleNamespace(max_upload_mb=21)
        self.max_upload_size_mb = 84
        self.upload_chunk_size = 512
        self.ai_confidence_threshold = 0.91


def test_get_ai_confidence_threshold_from_nested():
    cfg = Dummy()
    assert config_helpers.get_ai_confidence_threshold(cfg) == 0.9


def test_get_ai_confidence_threshold_alt_attrs():
    cfg = SimpleNamespace(ai_threshold=0.88)
    assert config_helpers.get_ai_confidence_threshold(cfg) == 0.88
    cfg = {"ai_confidence_threshold": 0.77}
    assert config_helpers.get_ai_confidence_threshold(cfg) == 0.77


def test_get_ai_confidence_threshold_default():
    assert config_helpers.get_ai_confidence_threshold(None) == 0.8


def test_get_max_upload_size_mb_attrs():
    cfg = Dummy()
    assert config_helpers.get_max_upload_size_mb(cfg) == 84


def test_get_max_upload_size_mb_alt_attrs():
    cfg = SimpleNamespace(max_size_mb=33)
    assert config_helpers.get_max_upload_size_mb(cfg) == 33
    cfg = SimpleNamespace(security=SimpleNamespace(max_upload_mb=77))
    assert config_helpers.get_max_upload_size_mb(cfg) == 77
    cfg = {"max_upload_size_mb": 55}
    assert config_helpers.get_max_upload_size_mb(cfg) == 55


def test_get_max_upload_size_mb_default():
    assert config_helpers.get_max_upload_size_mb(None) == 100


def test_get_upload_chunk_size_attrs():
    cfg = Dummy()
    assert config_helpers.get_upload_chunk_size(cfg) == 512


def test_get_upload_chunk_size_alt_attrs():
    cfg = SimpleNamespace(chunk_size=1024)
    assert config_helpers.get_upload_chunk_size(cfg) == 1024
    cfg = SimpleNamespace(uploads=SimpleNamespace(DEFAULT_CHUNK_SIZE=256))
    assert config_helpers.get_upload_chunk_size(cfg) == 256
    cfg = {"upload_chunk_size": 128}
    assert config_helpers.get_upload_chunk_size(cfg) == 128


def test_get_upload_chunk_size_default():
    assert config_helpers.get_upload_chunk_size(None) == 50000


def test_configuration_service_integration():
    from yosai_intel_dashboard.src.services.configuration_service import (
        DynamicConfigurationService,
    )
    from src.common.config import ConfigService

    cfg = ConfigService(
        {
            "ai_confidence_threshold": 0.66,
            "max_upload_size_mb": 123,
            "upload_chunk_size": 987,
        }
    )
    service = DynamicConfigurationService(cfg=cfg)
    assert service.ai_confidence_threshold == 0.66
    assert service.max_upload_size_mb == 123
    assert service.upload_chunk_size == 987
