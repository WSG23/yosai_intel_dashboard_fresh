import sys
import time
from pathlib import Path

from core.plugins.manager import PluginManager
from core.container import Container as DIContainer
from config.config import ConfigManager


class SimplePlugin:
    class metadata:
        name = "simple"

    def __init__(self):
        self.started = False
        self.load_config = None

    def load(self, container, config):
        self.load_config = config
        container.register("simple_service", object())
        return True

    def configure(self, config):
        return True

    def start(self):
        self.started = True
        return True

    def stop(self):
        self.started = False
        return True

    def health_check(self):
        return {"healthy": True}


def test_load_plugin_registers_plugin(tmp_path):
    cfg_manager = ConfigManager()
    cfg_manager.config.plugins = {"simple": {"enabled": True}}
    manager = PluginManager(DIContainer(), cfg_manager, health_check_interval=1)
    plugin = SimplePlugin()
    assert manager.load_plugin(plugin) is True
    assert plugin.load_config == {"enabled": True}
    assert "simple" in manager.plugins
    health = manager.get_plugin_health()
    assert health["simple"]["health"] == {"healthy": True}
    manager.stop_health_monitor()


def test_load_all_plugins(tmp_path):
    pkg_dir = tmp_path / "sampleplugins"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    plugin_file = pkg_dir / "plug.py"
    plugin_file.write_text(
        """
class Plug:
    class metadata:
        name = 'auto'
    def __init__(self):
        self.config = None
    def load(self, c, conf):
        self.config = conf
        return True
    def configure(self, conf):
        return True
    def start(self):
        return True
    def stop(self):
        return True
    def health_check(self):
        return {'healthy': True}

def create_plugin():
    return Plug()
"""
    )
    sys.path.insert(0, str(tmp_path))
    try:
        cfg_mgr = ConfigManager()
        cfg_mgr.config.plugins = {"auto": {"flag": 1}}
        manager = PluginManager(DIContainer(), cfg_mgr, package="sampleplugins", health_check_interval=1)
        plugins = manager.load_all_plugins()
        assert len(plugins) == 1
        assert "auto" in manager.plugins
        assert plugins[0].config == {"flag": 1}
    finally:
        sys.path.remove(str(tmp_path))
        manager.stop_health_monitor()


def test_get_plugin_health_snapshot():
    cfg_mgr = ConfigManager()
    cfg_mgr.config.plugins = {"simple": {"x": 2}}
    manager = PluginManager(DIContainer(), cfg_mgr, health_check_interval=1)
    plugin = SimplePlugin()
    manager.load_plugin(plugin)
    assert plugin.load_config == {"x": 2}
    time.sleep(1.2)
    snapshot = manager.health_snapshot
    assert "simple" in snapshot
    assert snapshot["simple"]["health"] == {"healthy": True}
    manager.stop_health_monitor()
