import time
from core.plugins.manager import PluginManager
from core.container import Container as DIContainer
from config.config import ConfigManager


def test_health_monitor_thread_stops():
    manager = PluginManager(DIContainer(), ConfigManager(), health_check_interval=0.01)
    time.sleep(0.05)
    assert manager._health_thread.is_alive()
    manager.stop_health_monitor()
    assert not manager._health_thread.is_alive()
