import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType, SimpleNamespace
from tests.import_helpers import safe_import, import_optional

# stub config.dynamic_config for PerformanceMonitor
cfg = ModuleType("config")
cfg.dynamic_config = SimpleNamespace(
    performance=SimpleNamespace(memory_usage_threshold_mb=1024)
)
safe_import('config', cfg)
safe_import('config.dynamic_config', cfg)

# minimal ModelMetrics stub used by detect_model_drift
mpm_stub = ModuleType("monitoring.model_performance_monitor")


@dataclass
class ModelMetrics:
    accuracy: float
    precision: float
    recall: float


mpm_stub.ModelMetrics = ModelMetrics
safe_import('monitoring.model_performance_monitor', mpm_stub)

# create minimal package structure for core
core_pkg = ModuleType("core")
core_pkg.__path__ = []  # mark as package
safe_import('core', core_pkg)

# load dependencies used by performance.py
for name in ["base_model", "cpu_optimizer", "memory_manager"]:
    spec = importlib.util.spec_from_file_location(
        f"core.{name}", Path("core") / f"{name}.py"
    )
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = "core"
    sys.modules[f"core.{name}"] = mod
    spec.loader.exec_module(mod)

spec = importlib.util.spec_from_file_location(
    "core.performance", Path("core/performance.py")
)
perf = importlib.util.module_from_spec(spec)
perf.__package__ = "core"
safe_import('core.performance', perf)
spec.loader.exec_module(perf)

PerformanceMonitor = perf.PerformanceMonitor


def test_detect_model_drift():
    monitor = PerformanceMonitor(max_metrics=10)
    monitor.aggregated_metrics = {
        "model.accuracy": [0.8],
        "model.precision": [0.9],
        "model.recall": [0.95],
    }
    baseline = ModelMetrics(1.0, 1.0, 1.0)
    assert monitor.detect_model_drift(baseline, threshold=0.1)
    monitor.aggregated_metrics = {
        "model.accuracy": [0.98],
        "model.precision": [0.99],
        "model.recall": [1.0],
    }
    assert not monitor.detect_model_drift(baseline, threshold=0.1)
