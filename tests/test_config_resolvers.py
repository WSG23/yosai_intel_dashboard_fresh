import importlib.util
from pathlib import Path
from types import SimpleNamespace


spec = importlib.util.spec_from_file_location(
    "utils.config_resolvers",
    Path(__file__).resolve().parents[1]
    / "yosai_intel_dashboard"
    / "src"
    / "utils"
    / "config_resolvers.py",
)
config_resolvers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_resolvers)


class Dummy:
    def __init__(self):
        self.performance = SimpleNamespace(ai_confidence_threshold=0.9)
        self.upload = SimpleNamespace(max_file_size_mb=42)
        self.uploads = SimpleNamespace(DEFAULT_CHUNK_SIZE=256)
        self.chunk_size = 512
        self.max_size_mb = 84
        self.security = SimpleNamespace(max_upload_mb=21)
        self.ai_threshold = 0.95


def test_resolve_ai_confidence_threshold_from_cfg_attrs():
    cfg = Dummy()
    assert config_resolvers.resolve_ai_confidence_threshold(cfg) == 0.9


def test_resolve_ai_confidence_threshold_alt_attr():
    cfg = SimpleNamespace(ai_threshold=0.88)
    assert config_resolvers.resolve_ai_confidence_threshold(cfg) == 0.88


def test_resolve_ai_confidence_threshold_default():
    assert (
        config_resolvers.resolve_ai_confidence_threshold(
            None, default_resolver=lambda: 0.75
        )
        == 0.75
    )


def test_resolve_max_upload_size_mb_all_attrs():
    cfg = Dummy()
    assert config_resolvers.resolve_max_upload_size_mb(cfg) == 84


def test_resolve_max_upload_size_mb_alt_attrs():
    cfg = SimpleNamespace(max_size_mb=33)
    assert config_resolvers.resolve_max_upload_size_mb(cfg) == 33
    cfg = SimpleNamespace(security=SimpleNamespace(max_upload_mb=77))
    assert config_resolvers.resolve_max_upload_size_mb(cfg) == 77


def test_resolve_max_upload_size_mb_default():
    assert (
        config_resolvers.resolve_max_upload_size_mb(
            None, default_resolver=lambda: 10
        )
        == 10
    )


def test_resolve_upload_chunk_size_attrs():
    cfg = Dummy()
    assert config_resolvers.resolve_upload_chunk_size(cfg) == 512


def test_resolve_upload_chunk_size_alt_attr():
    cfg = SimpleNamespace(chunk_size=1024)
    assert config_resolvers.resolve_upload_chunk_size(cfg) == 1024


def test_resolve_upload_chunk_size_default():
    assert (
        config_resolvers.resolve_upload_chunk_size(
            None, default_resolver=lambda: 128
        )
        == 128
    )
