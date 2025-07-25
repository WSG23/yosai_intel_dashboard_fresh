import time

from yosai_intel_dashboard.src.core.plugins.manager import (
    ThreadSafePluginManager as PluginManager,
)
from yosai_intel_dashboard.src.core.service_container import ServiceContainer
from yosai_intel_dashboard.src.infrastructure.config import create_config_manager


def test_health_thread_stops_on_exit():
    mgr = PluginManager(
        ServiceContainer(), create_config_manager(), health_check_interval=1
    )
    assert mgr._health_thread.is_alive()
    mgr.stop_health_monitor()
    time.sleep(0.1)
    assert not mgr._health_thread.is_alive()


def test_context_manager_stops_thread():
    with PluginManager(
        ServiceContainer(), create_config_manager(), health_check_interval=1
    ) as mgr:
        assert mgr._health_thread.is_alive()
    time.sleep(0.1)
    assert not mgr._health_thread.is_alive()
