from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

# Minimal pandas stub
pd_stub = types.SimpleNamespace(DataFrame=object)
sys.modules["pandas"] = pd_stub

# Stub utils.upload_store
utils_pkg = types.ModuleType("yosai_intel_dashboard.src.utils")
utils_pkg.__path__ = []
upload_store_mod = types.ModuleType("upload_store")


def _store():
    class Store:
        def get_all_data(self):
            return {}
    return Store()

upload_store_mod.get_uploaded_data_store = _store
sys.modules["yosai_intel_dashboard.src.utils"] = utils_pkg
sys.modules["yosai_intel_dashboard.src.utils.upload_store"] = upload_store_mod

# Prepare package hierarchy to support relative imports without executing __init__
root = Path(__file__).resolve().parents[1]
package_paths = {
    "yosai_intel_dashboard": root / "yosai_intel_dashboard",
    "yosai_intel_dashboard.src": root / "yosai_intel_dashboard/src",
    "yosai_intel_dashboard.src.services": root / "yosai_intel_dashboard/src/services",
    "yosai_intel_dashboard.src.services.upload": root / "yosai_intel_dashboard/src/services/upload",
}
for name, path in package_paths.items():
    if name not in sys.modules:
        mod = types.ModuleType(name)
        mod.__path__ = [str(path)]
        sys.modules[name] = mod

module_name = "yosai_intel_dashboard.src.services.upload.upload_processing"
file_path = package_paths["yosai_intel_dashboard.src.services.upload"] / "upload_processing.py"
spec = importlib.util.spec_from_file_location(module_name, file_path)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[module_name] = module
spec.loader.exec_module(module)
UploadAnalyticsProcessor = module.UploadAnalyticsProcessor


def test_get_analytics_from_uploaded_data_no_data(monkeypatch):
    proc = UploadAnalyticsProcessor(object(), object(), object(), object(), object())
    monkeypatch.setattr(proc, "load_uploaded_data", lambda: {})
    assert proc.get_analytics_from_uploaded_data() == {"status": "no_data"}

