from __future__ import annotations

import importlib.util
import os
import sys
import types
from pathlib import Path
from yosai_intel_dashboard.src.core.imports.resolver import safe_import

if "services.resilience" not in sys.modules:
    safe_import('services.resilience', types.ModuleType("services.resilience"))
if "services.resilience.metrics" not in sys.modules:
    metrics_stub = types.ModuleType("services.resilience.metrics")
    metrics_stub.circuit_breaker_state = types.SimpleNamespace(
        labels=lambda *a, **k: types.SimpleNamespace(inc=lambda *a, **k: None)
    )
    safe_import('services.resilience.metrics', metrics_stub)

import pandas as pd

FS_PATH = Path(__file__).resolve().parents[1] / "models" / "ml" / "feature_store.py"
spec = importlib.util.spec_from_file_location("feature_store", FS_PATH)
fs_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fs_mod)
FeastFeatureStore = fs_mod.FeastFeatureStore


class DummyService:  # minimal placeholder
    pass


anomaly_service = DummyService()


def test_feature_store_init():
    os.makedirs("feature_store/data/feature_repo", exist_ok=True)
    fs = FeastFeatureStore(repo_path="feature_store")
    assert fs.store is not None


def test_monitor_feature_drift():
    fs = FeastFeatureStore(repo_path="feature_store")
    base = pd.DataFrame({"x": [1, 2, 3]})
    new = pd.DataFrame({"x": [2, 3, 4]})
    drifts = fs.monitor_feature_drift(new, base, threshold=0.5)
    assert "x" in drifts


if __name__ == "__main__":
    test_feature_store_init()
    test_monitor_feature_drift()
    print("Feature store tests passed")
