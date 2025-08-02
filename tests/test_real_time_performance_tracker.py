import importlib.util
import os
import sys
import types
from pathlib import Path

os.environ.setdefault("CACHE_TTL", "1")
os.environ.setdefault("CACHE_TTL_SECONDS", "1")
os.environ.setdefault("JWKS_CACHE_TTL", "1")


def _load_tracker(perf):
    pkg_names = [
        "yosai_intel_dashboard",
        "yosai_intel_dashboard.src",
        "yosai_intel_dashboard.src.core",
        "yosai_intel_dashboard.src.core.monitoring",
    ]
    for name in pkg_names:
        sys.modules.setdefault(name, types.ModuleType(name))

    base_model_mod = types.ModuleType("yosai_intel_dashboard.src.core.base_model")
    class BaseModel:
        def __init__(self, *a, **k):
            pass
    base_model_mod.BaseModel = BaseModel
    performance_mod = types.ModuleType("yosai_intel_dashboard.src.core.performance")
    class MetricType:
        FILE_PROCESSING = "fp"
        EXECUTION_TIME = "et"
    performance_mod.MetricType = MetricType
    performance_mod.get_performance_monitor = lambda: perf
    sys.modules["yosai_intel_dashboard.src.core.base_model"] = base_model_mod
    sys.modules["yosai_intel_dashboard.src.core.performance"] = performance_mod

    path = Path(__file__).resolve().parents[1] / "yosai_intel_dashboard" / "src" / "core" / "monitoring" / "real_time_performance_tracker.py"
    spec = importlib.util.spec_from_file_location(
        "yosai_intel_dashboard.src.core.monitoring.real_time_performance_tracker",
        path,
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)  # type: ignore
    return module.RealTimePerformanceTracker, performance_mod.MetricType


def test_tracker_records_latency_and_throughput():
    calls = []
    perf = types.SimpleNamespace(
        record_metric=lambda n, v, t, metadata=None: calls.append((n, v, t, metadata))
    )
    Tracker, MetricType = _load_tracker(perf)
    tracker = Tracker()
    tracker.record_upload_speed(5.0, 2.0)
    tracker.record_callback_duration("cb", 0.25)
    assert (
        "upload.speed_mb_s",
        2.5,
        MetricType.FILE_PROCESSING,
        {"file_size_mb": 5.0, "duration_sec": 2.0},
    ) in calls
    assert (
        "callback.cb.duration",
        0.25,
        MetricType.EXECUTION_TIME,
        None,
    ) in calls
