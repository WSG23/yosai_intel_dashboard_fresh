import importlib.util
import os
import types
from pathlib import Path

import pandas as pd

os.environ.setdefault("CACHE_TTL", "1")
os.environ.setdefault("CACHE_TTL_SECONDS", "1")
os.environ.setdefault("JWKS_CACHE_TTL", "1")

path = (
    Path(__file__).resolve().parents[1]
    / "yosai_intel_dashboard"
    / "src"
    / "models"
    / "ml"
    / "model_registry.py"
)
spec = importlib.util.spec_from_file_location("model_registry", path)
mr = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(mr)
ModelRegistry = mr.ModelRegistry


class DummyS3:
    def upload_file(self, *a, **k):
        pass

    def download_file(self, *a, **k):
        pass


def test_get_drift_metrics_uses_compute_psi(monkeypatch):
    registry = ModelRegistry("sqlite:///:memory:", bucket="b", s3_client=DummyS3())
    base = pd.DataFrame({"a": [0, 1, 2]})
    cur = pd.DataFrame({"a": [1, 2, 3]})
    registry.log_features("m", base)
    registry.log_features("m", cur)

    called = {}

    def fake_compute_psi(baseline, current, bins=10):
        called["baseline"] = baseline
        called["current"] = current
        called["bins"] = bins
        return {"a": 0.1}

    monkeypatch.setattr(
        "yosai_intel_dashboard.src.services.monitoring.drift.compute_psi",
        fake_compute_psi,
    )

    metrics = registry.get_drift_metrics("m")
    assert called["baseline"].equals(base)
    assert called["current"].equals(cur)
    assert metrics == {"a": 0.1}
