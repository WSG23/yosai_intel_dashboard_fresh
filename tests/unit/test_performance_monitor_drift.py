import sys
from types import ModuleType, SimpleNamespace
from yosai_intel_dashboard.src.core.imports.resolver import safe_import

# minimal config stub
cfg_mod = ModuleType("config")


class DatabaseSettings:
    def __init__(self, type: str = "sqlite", **_: object) -> None:
        self.type = type


cfg_mod.DatabaseSettings = DatabaseSettings
cfg_mod.dynamic_config = SimpleNamespace(
    performance=SimpleNamespace(memory_usage_threshold_mb=1024)
)
safe_import('config', cfg_mod)
safe_import('config.dynamic_config', cfg_mod)

import importlib.util
from pathlib import Path

core_pkg = ModuleType("core")
core_pkg.__path__ = [str(Path(__file__).resolve().parents[1] / "core")]
safe_import('core', core_pkg)

spec = importlib.util.spec_from_file_location(
    "core.performance", Path(__file__).resolve().parents[1] / "core" / "performance.py"
)
perf_module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = perf_module
spec.loader.exec_module(perf_module)  # type: ignore
PerformanceMonitor = perf_module.PerformanceMonitor


def test_detect_model_drift():
    monitor = PerformanceMonitor()
    baseline = {"accuracy": 1.0, "precision": 0.5, "recall": 0.5}
    metrics = {"accuracy": 0.85, "precision": 0.55, "recall": 0.5}
    assert monitor.detect_model_drift(metrics, baseline, drift_threshold=0.1)
    metrics_ok = {"accuracy": 0.95, "precision": 0.55, "recall": 0.5}
    assert not monitor.detect_model_drift(metrics_ok, baseline, drift_threshold=0.1)
