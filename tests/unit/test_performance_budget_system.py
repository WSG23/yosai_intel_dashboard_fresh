import importlib.util
import os
import sys
import types
from pathlib import Path

os.environ.setdefault("CACHE_TTL", "1")
os.environ.setdefault("CACHE_TTL_SECONDS", "1")
os.environ.setdefault("JWKS_CACHE_TTL", "1")


def _load_system():
    pkg_names = [
        "yosai_intel_dashboard",
        "yosai_intel_dashboard.src",
        "yosai_intel_dashboard.src.core",
        "yosai_intel_dashboard.src.core.monitoring",
    ]
    for name in pkg_names:
        sys.modules.setdefault(name, types.ModuleType(name))

    perf_mod = types.ModuleType("yosai_intel_dashboard.src.core.performance")
    perf_mod.get_performance_monitor = lambda: types.SimpleNamespace(metrics=[])
    sys.modules["yosai_intel_dashboard.src.core.performance"] = perf_mod

    uem_mod = types.ModuleType(
        "yosai_intel_dashboard.src.core.monitoring.user_experience_metrics"
    )
    class AlertDispatcher:
        pass
    uem_mod.AlertDispatcher = AlertDispatcher
    sys.modules[
        "yosai_intel_dashboard.src.core.monitoring.user_experience_metrics"
    ] = uem_mod

    path = Path(__file__).resolve().parents[1] / "yosai_intel_dashboard" / "src" / "core" / "monitoring" / "performance_budget_system.py"
    spec = importlib.util.spec_from_file_location(
        "yosai_intel_dashboard.src.core.monitoring.performance_budget_system",
        path,
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)  # type: ignore
    return module.PerformanceBudgetSystem


def test_alert_triggered_on_budget_exceeded():
    System = _load_system()
    calls = []
    dispatcher = types.SimpleNamespace(send_alert=lambda msg: calls.append(msg))
    system = System({"latency": 1.0}, dispatcher)
    system.check_metric("latency", 1.5)
    system.check_metric("latency", 0.5)
    assert calls == ["latency exceeded budget: 1.50 > 1.00"]
