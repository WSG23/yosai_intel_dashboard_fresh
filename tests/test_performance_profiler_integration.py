from core.performance import profiler, get_performance_monitor
from yosai_intel_dashboard.src.infrastructure.config.dynamic_config import dynamic_config


def clear_monitor():
    monitor = get_performance_monitor()
    monitor.metrics.clear()
    monitor.aggregated_metrics.clear()
    return monitor


def test_profiler_records_metrics_via_monitor():
    dynamic_config.performance.profiling_enabled = True
    monitor = clear_monitor()

    profiler.start_profiling("sess")
    profiler.profile_function("sess", "func", 0.1)
    profiler.end_profiling("sess")

    report = monitor.get_profiler_report("sess")
    assert report["function_count"] == 2  # session + function
    assert "func" in report["functions"]
    assert report["functions"]["func"]["calls"] == 1


def test_profiler_respects_disabled_toggle():
    dynamic_config.performance.profiling_enabled = False
    monitor = clear_monitor()

    profiler.start_profiling("sess2")
    profiler.profile_function("sess2", "func2", 0.2)
    profiler.end_profiling("sess2")

    report = monitor.get_profiler_report("sess2")
    assert report["function_count"] == 0
    assert report["functions"] == {}
