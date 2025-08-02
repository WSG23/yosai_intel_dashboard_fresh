import importlib.util
import sys

from yosai_intel_dashboard.src.core import performance
from yosai_intel_dashboard.src.core.performance import PerformanceMonitor

spec = importlib.util.spec_from_file_location(
    "monitoring.ui_monitor", "monitoring/ui_monitor.py"
)
ui_module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = ui_module
spec.loader.exec_module(ui_module)  # type: ignore
RealTimeUIMonitor = ui_module.RealTimeUIMonitor


def test_ui_monitor_records(monkeypatch):
    monitor = PerformanceMonitor(max_metrics=10)
    monkeypatch.setattr(performance, "_performance_monitor", monitor)

    ui = RealTimeUIMonitor()
    ui.record_frame_time(10.0)
    ui.record_callback_duration("cb", 0.02)

    names = [m.name for m in monitor.metrics]
    assert "ui.frame_time_ms" in names
    assert "ui.callback.cb" in names
