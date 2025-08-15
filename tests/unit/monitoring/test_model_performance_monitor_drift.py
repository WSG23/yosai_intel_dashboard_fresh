import sys
import types
from types import SimpleNamespace

from yosai_intel_dashboard.src.core.imports.resolver import safe_import

# minimal config stub to avoid heavy imports
cfg_mod = types.ModuleType("config")


class DatabaseSettings:
    def __init__(self, type: str = "sqlite", **_: object) -> None:
        self.type = type


cfg_mod.DatabaseSettings = DatabaseSettings
cfg_mod.dynamic_config = SimpleNamespace(
    performance=SimpleNamespace(memory_usage_threshold_mb=1024)
)
safe_import("config", cfg_mod)
safe_import("config.dynamic_config", cfg_mod)

# minimal performance monitor stub
perf_mod = types.ModuleType("core.performance")


class MetricType(SimpleNamespace):
    FILE_PROCESSING = "file"


perf_mod.MetricType = MetricType
perf_mod.get_performance_monitor = lambda: SimpleNamespace(
    record_metric=lambda *a, **k: None, aggregated_metrics={}
)
safe_import("core.performance", perf_mod)

# extend prometheus metrics stub
prom_mod = types.ModuleType("monitoring.prometheus.model_metrics")
prom_mod.update_model_metrics = lambda *a, **k: None
prom_mod.start_model_metrics_server = lambda *a, **k: None
safe_import("monitoring.prometheus.model_metrics", prom_mod)

# Stub services.resilience.metrics to avoid heavy deps
metrics_mod = types.ModuleType("services.resilience.metrics")
metrics_mod.circuit_breaker_state = SimpleNamespace(
    labels=lambda *a, **k: SimpleNamespace(inc=lambda *a, **k: None)
)
resilience_pkg = types.ModuleType("services.resilience")
resilience_pkg.metrics = metrics_mod
safe_import("services", types.ModuleType("services"))
safe_import("services.resilience", resilience_pkg)
safe_import("services.resilience.metrics", metrics_mod)

from yosai_intel_dashboard.src.infrastructure.monitoring import (
    model_performance_monitor as mpm,
)


def test_relative_drift_detection():
    baseline = mpm.ModelMetrics(accuracy=1.0, precision=0.5, recall=0.5)
    monitor = mpm.ModelPerformanceMonitor(baseline=baseline, drift_threshold=0.1)
    metrics = mpm.ModelMetrics(accuracy=0.85, precision=0.55, recall=0.5)
    assert monitor.detect_drift(metrics)
    metrics_ok = mpm.ModelMetrics(accuracy=0.95, precision=0.55, recall=0.5)
    assert not monitor.detect_drift(metrics_ok)


def test_metrics_server_started(monkeypatch):
    called = []
    monkeypatch.setattr(mpm, "start_model_metrics_server", lambda: called.append(True))
    mpm._model_performance_monitor = None
    monitor = mpm.get_model_performance_monitor()
    assert called
    assert isinstance(monitor, mpm.ModelPerformanceMonitor)
