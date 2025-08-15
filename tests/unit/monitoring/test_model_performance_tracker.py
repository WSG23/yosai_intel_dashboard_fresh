from __future__ import annotations

import os

import pandas as pd
import pytest

os.environ.setdefault("LIGHTWEIGHT_SERVICES", "1")

from yosai_intel_dashboard.src.infrastructure.monitoring.model_performance_tracker import (
    ModelPerformanceTracker,
)


def test_metric_collection():
    tracker = ModelPerformanceTracker()
    snap = tracker.record_batch([1, 0, 1, 1], [1, 0, 0, 1], latency=0.2)
    assert snap.accuracy == pytest.approx(0.75)
    assert snap.f1 == pytest.approx(0.8)
    assert snap.throughput == pytest.approx(20.0)
    assert len(tracker.metrics_history) == 1


def test_drift_calculation():
    tracker = ModelPerformanceTracker()
    base = pd.DataFrame({"a": [0, 1, 0, 1]})
    current = pd.DataFrame({"a": [0, 0, 0, 0]})
    drift = tracker.calculate_drift(base, current)
    assert "a" in drift
    assert set(drift["a"].keys()) == {"psi", "ks", "wasserstein"}


def test_feature_importance_tracking():
    tracker = ModelPerformanceTracker(drift_threshold=0.1)
    baseline = {"f1": 0.5, "f2": 0.5}
    assert not tracker.update_feature_importance(baseline)
    changed = {"f1": 0.7, "f2": 0.3}
    assert tracker.update_feature_importance(changed)
    assert len(tracker.feature_importance_history) == 2
