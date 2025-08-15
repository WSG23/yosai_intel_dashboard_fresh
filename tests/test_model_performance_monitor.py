import sys
from datetime import datetime
from types import ModuleType, SimpleNamespace

from yosai_intel_dashboard.src.core.imports.resolver import safe_import

# minimal config stub to avoid heavy imports
cfg_mod = ModuleType("config")


class DatabaseSettings:
    def __init__(self, type: str = "sqlite", **_: object) -> None:
        self.type = type


cfg_mod.DatabaseSettings = DatabaseSettings
cfg_mod.dynamic_config = SimpleNamespace(
    performance=SimpleNamespace(memory_usage_threshold_mb=1024)
)
safe_import("config", cfg_mod)
safe_import("yosai_intel_dashboard.src.config", cfg_mod)
safe_import("config.dynamic_config", cfg_mod)
safe_import("yosai_intel_dashboard.src.config.dynamic_config", cfg_mod)

# minimal performance monitor stub
perf_mod = ModuleType("core.performance")


class MetricType(SimpleNamespace):
    FILE_PROCESSING = "file"


perf_mod.MetricType = MetricType
perf_mod.get_performance_monitor = lambda: SimpleNamespace(
    record_metric=lambda *a, **k: None, aggregated_metrics={}
)
safe_import("core.performance", perf_mod)
safe_import("yosai_intel_dashboard.src.core.performance", perf_mod)

# extend prometheus metrics stub
prom_mod = ModuleType("monitoring.prometheus.model_metrics")
prom_mod.update_model_metrics = lambda *a, **k: None
prom_mod.start_model_metrics_server = lambda *a, **k: None
safe_import("monitoring.prometheus.model_metrics", prom_mod)
safe_import("yosai_intel_dashboard.src.infrastructure.monitoring.prometheus.model_metrics", prom_mod)

# stub services.resilience.metrics to avoid heavy deps
metrics_mod = ModuleType("services.resilience.metrics")
metrics_mod.circuit_breaker_state = SimpleNamespace(
    labels=lambda *a, **k: SimpleNamespace(inc=lambda: None)
)
resilience_pkg = ModuleType("services.resilience")
resilience_pkg.metrics = metrics_mod
safe_import("services", ModuleType("services"))
safe_import("yosai_intel_dashboard.src.services", ModuleType("services"))
safe_import("services.resilience", resilience_pkg)
safe_import("yosai_intel_dashboard.src.services.resilience", resilience_pkg)
safe_import("services.resilience.metrics", metrics_mod)
safe_import("yosai_intel_dashboard.src.services.resilience.metrics", metrics_mod)

from yosai_intel_dashboard.src.infrastructure.monitoring import (
    model_performance_monitor as mpm,
)


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
    monitor.log_prediction("h", {"x": 1}, "1", timestamp=ts)

    event = records[0]
    assert event["input_hash"] == "h"
    assert event["prediction"] == {"x": 1}
    assert event["timestamp"] == ts.isoformat()
    assert event["model_version"] == "1"


def test_detect_drift():
    baseline = mpm.ModelMetrics(accuracy=0.9, precision=0.8, recall=0.7)
    monitor = mpm.ModelPerformanceMonitor(baseline=baseline, drift_threshold=0.05)
    metrics_ok = mpm.ModelMetrics(accuracy=0.92, precision=0.8, recall=0.7)
    assert not monitor.detect_drift(metrics_ok)
    metrics_bad = mpm.ModelMetrics(accuracy=0.7, precision=0.8, recall=0.7)
    assert monitor.detect_drift(metrics_bad)
