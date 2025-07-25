import pandas as pd
import importlib.util
from pathlib import Path
import os

FS_PATH = Path(__file__).resolve().parents[1] / "models" / "ml" / "feature_store.py"
spec = importlib.util.spec_from_file_location("feature_store", FS_PATH)
fs_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fs_mod)
FeastFeatureStore = fs_mod.FeastFeatureStore

ANOMALY_PATH = Path(__file__).resolve().parents[1] / "feature_store" / "anomaly_features.py"
spec2 = importlib.util.spec_from_file_location("anomaly_features", ANOMALY_PATH)
af_mod = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(af_mod)
anomaly_service = af_mod.anomaly_service


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
