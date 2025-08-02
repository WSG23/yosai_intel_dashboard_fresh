from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from tests.import_helpers import safe_import, import_optional

stub_utils = ModuleType("utils")
stub_utils.__path__ = []

stub_core = ModuleType("core.config")
stub_core.get_ai_confidence_threshold = lambda: 0.75
stub_core.get_max_upload_size_mb = lambda: 10
stub_core.get_upload_chunk_size = lambda: 128
stub_core_pkg = ModuleType("core")
stub_core_pkg.__path__ = []
stub_core_pkg.config = stub_core
safe_import('core', stub_core_pkg)
safe_import('core.config', stub_core)

stub_config_pkg = ModuleType("config")
stub_config_pkg.__path__ = []
safe_import('config', stub_config_pkg)

spec_resolvers = importlib.util.spec_from_file_location(
    "utils.config_resolvers",
    Path(__file__).resolve().parents[1] / "utils" / "config_resolvers.py",
)
config_resolvers = importlib.util.module_from_spec(spec_resolvers)
spec_resolvers.loader.exec_module(config_resolvers)
stub_utils.config_resolvers = config_resolvers
safe_import('utils', stub_utils)
safe_import('utils.config_resolvers', config_resolvers)

spec_utils = importlib.util.spec_from_file_location(
    "config.utils", Path(__file__).resolve().parents[1] / "config" / "utils.py"
)
config_utils = importlib.util.module_from_spec(spec_utils)
spec_utils.loader.exec_module(config_utils)


def test_get_ai_confidence_threshold_from_cfg():
    cfg = SimpleNamespace(ai_threshold=0.55)
    assert config_utils.get_ai_confidence_threshold(cfg) == 0.55


def test_get_upload_chunk_size_from_cfg():
    cfg = SimpleNamespace(chunk_size=256)
    assert config_utils.get_upload_chunk_size(cfg) == 256
