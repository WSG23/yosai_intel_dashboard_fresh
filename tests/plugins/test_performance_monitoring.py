import time
import types

from yosai_intel_dashboard.src.infrastructure.di.service_container import ServiceContainer
from tests.plugins.test_plugin_manager import _install_protocol_stubs


class FakeProc:
    def cpu_percent(self, interval=None):
        return 80.0

    def memory_info(self):
        return type("mem", (), {"rss": 200 * 1024 * 1024})()


def test_monitoring_alerts(monkeypatch):
    _install_protocol_stubs(monkeypatch)
    from core.plugins.performance_manager import EnhancedThreadSafePluginManager

    class DummyConfig:
        def __init__(self):
            self.config = types.SimpleNamespace(plugin_settings={})

        def get_plugin_config(self, name: str):
            return {}

    monkeypatch.setattr("psutil.Process", lambda: FakeProc())
    monkeypatch.setattr("core.plugins.performance_manager.time.sleep", lambda n: None)
    mgr = EnhancedThreadSafePluginManager(
        ServiceContainer(), DummyConfig(), health_check_interval=0.1
    )
    mgr._monitor_interval = 0
    mgr.performance_manager.performance_thresholds["cpu_usage"] = 10
    mgr.performance_manager.performance_thresholds["memory_usage"] = 50
    time.sleep(0.001)
    mgr._perf_monitor_active = False
    mgr._perf_thread.join(timeout=0)
    mgr.stop_health_monitor()
    alerts = mgr.performance_manager.alert_history
    assert any(a["metric"] == "cpu_usage" for a in alerts)
    assert any(a["metric"] == "memory_usage" for a in alerts)
