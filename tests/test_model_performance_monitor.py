from types import SimpleNamespace, ModuleType
import sys
from datetime import datetime

# stub services.resilience.metrics to avoid heavy deps
metrics_mod = ModuleType("services.resilience.metrics")
metrics_mod.circuit_breaker_state = SimpleNamespace(labels=lambda *a, **k: SimpleNamespace(inc=lambda: None))
resilience_pkg = ModuleType("services.resilience")
resilience_pkg.metrics = metrics_mod
sys.modules.setdefault("services", ModuleType("services"))
sys.modules.setdefault("services.resilience", resilience_pkg)
sys.modules.setdefault("services.resilience.metrics", metrics_mod)

import monitoring.model_performance_monitor as mpm


class DummyMonitor:
    def __init__(self):
        self.metrics = []

    def record_metric(self, name, value, mtype):
        self.metrics.append((name, value, mtype))


def test_log_metrics(monkeypatch):
    perf = DummyMonitor()
    monkeypatch.setattr(mpm, "get_performance_monitor", lambda: perf)
    called = []
    monkeypatch.setattr(mpm, "update_model_metrics", lambda m: called.append(True))

    monitor = mpm.ModelPerformanceMonitor()
    metrics = mpm.ModelMetrics(accuracy=1.0, precision=0.9, recall=0.8)
    monitor.log_metrics(metrics)

    assert len(perf.metrics) == 3
    assert called


def test_log_prediction():
    records = []
    logger = SimpleNamespace(info=lambda msg, extra=None: records.append(extra))
    monitor = mpm.ModelPerformanceMonitor(logger=logger)
    ts = datetime(2024, 1, 1)
    monitor.log_prediction("h", {"x": 1}, timestamp=ts)

    event = records[0]
    assert event["input_hash"] == "h"
    assert event["prediction"] == {"x": 1}
    assert event["timestamp"] == ts.isoformat()


def test_detect_drift():
    baseline = mpm.ModelMetrics(accuracy=0.9, precision=0.8, recall=0.7)
    monitor = mpm.ModelPerformanceMonitor(baseline=baseline, drift_threshold=0.05)
    metrics_ok = mpm.ModelMetrics(accuracy=0.92, precision=0.8, recall=0.7)
    assert not monitor.detect_drift(metrics_ok)
    metrics_bad = mpm.ModelMetrics(accuracy=0.7, precision=0.8, recall=0.7)
    assert monitor.detect_drift(metrics_bad)
