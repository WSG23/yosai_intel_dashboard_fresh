from __future__ import annotations

import importlib.util
import logging
from pathlib import Path
from types import ModuleType
import sys

import pandas as pd
import pytest

# ensure a minimal 'feast' module is available
try:
    import feast  # noqa: F401
except Exception:  # pragma: no cover - environment missing feast
    feast = ModuleType("feast")

    class FeatureService:  # minimal placeholder
        pass

    class FeatureStore:  # minimal placeholder
        def __init__(self, repo_path: str, *_, **__):  # noqa: D401
            self.repo_path = repo_path

        def get_historical_features(self, *_, **__):  # pragma: no cover
            return None

        def get_online_features(self, *_, **__):  # pragma: no cover
            return None

    feast.FeatureService = FeatureService
    feast.FeatureStore = FeatureStore
    sys.modules["feast"] = feast

# load FeastFeatureStore from source file
FS_PATH = (
    Path(__file__).resolve().parents[2]
    / "yosai_intel_dashboard"
    / "src"
    / "models"
    / "ml"
    / "feature_store.py"
)
spec = importlib.util.spec_from_file_location("feature_store", FS_PATH)
fs_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fs_mod)
FeastFeatureStore = fs_mod.FeastFeatureStore


def test_monitor_feature_drift_calculates_scores_and_warns(caplog: pytest.LogCaptureFixture) -> None:
    fs = FeastFeatureStore(repo_path="feature_store")
    baseline = pd.DataFrame({"x": [1, 1, 1], "y": [1.0, 1.0, 1.0]})
    current = pd.DataFrame({"x": [2, 2, 2], "y": [1.2, 1.0, 0.9]})

    with caplog.at_level(logging.WARNING):
        drifts = fs.monitor_feature_drift(current, baseline, threshold=0.5)

    expected_y = abs(current["y"].mean() - baseline["y"].mean())
    assert drifts["x"] == pytest.approx(1.0)
    assert drifts["y"] == pytest.approx(expected_y)
    assert "Feature drift detected for x" in caplog.text
    assert "Feature drift detected for y" not in caplog.text
