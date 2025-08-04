import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "services.common.config_utils",
    Path(__file__).resolve().parents[1]
    / "yosai_intel_dashboard"
    / "src"
    / "services"
    / "common"
    / "config_utils.py",
)
config_utils = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_utils)


def test_common_init_applies_helpers():
    cfg = {
        "max_upload_size_mb": 42,
        "upload_chunk_size": 256,
        "ai_confidence_threshold": 0.9,
    }
    class Dummy:
        pass
    obj = Dummy()
    config_utils.common_init(obj, cfg)
    assert obj.max_size_mb == 42
    assert obj.chunk_size == 256
    assert obj.ai_threshold == 0.9
