import time
from core.plugins.manager import ThreadSafePluginManager as PluginManager
from core.container import Container as DIContainer
from config.config import ConfigManager


def test_health_thread_stops_on_exit():
    mgr = PluginManager(DIContainer(), ConfigManager(), health_check_interval=1)
    assert mgr._health_thread.is_alive()
    mgr.stop_health_monitor()
    time.sleep(0.1)
    assert not mgr._health_thread.is_alive()


def test_context_manager_stops_thread():
    with PluginManager(DIContainer(), ConfigManager(), health_check_interval=1) as mgr:
        assert mgr._health_thread.is_alive()
    time.sleep(0.1)
    assert not mgr._health_thread.is_alive()
