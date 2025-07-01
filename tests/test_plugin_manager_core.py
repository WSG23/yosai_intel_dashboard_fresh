import importlib
import sys
import types
from pathlib import Path

from core.plugins.manager import PluginManager
from core.container import Container as DIContainer
from config.config import ConfigManager
from core.plugins.protocols import PluginStatus


class DummyPlugin:
    """Simple plugin for testing"""

    class metadata:
        name = "dummy"

    def __init__(self):
        self.loaded = False
        self.started = False
        self.load_config = None

    def load(self, container, config):
        self.loaded = True
        self.load_config = config
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


class NoHealthPlugin:
    """Plugin missing health_check"""

    class metadata:
        name = "nohealth"

    def load(self, container, config):
        return True

    def configure(self, config):
        return True

    def start(self):
        return True

    def stop(self):
        return True


def test_load_plugin_success(tmp_path):
    cfg_mgr = ConfigManager()
    cfg_mgr.config.plugins = {"dummy": {"flag": 1}}
    manager = PluginManager(DIContainer(), cfg_mgr, health_check_interval=1)
    plugin = DummyPlugin()
    result = manager.load_plugin(plugin)

    assert plugin.load_config == {"flag": 1}

    assert result is True
    assert plugin.started
    assert "dummy" in manager.plugins
    assert manager.plugin_status["dummy"] == PluginStatus.STARTED
    manager.stop_health_monitor()


def test_load_plugin_failure_missing_health():
    manager = PluginManager(DIContainer(), ConfigManager(), health_check_interval=1)
    plugin = NoHealthPlugin()
    result = manager.load_plugin(plugin)

    assert result is False
    assert manager.plugin_status["nohealth"] == PluginStatus.FAILED
    manager.stop_health_monitor()


def test_get_plugin_health(monkeypatch):
    cfg_mgr = ConfigManager()
    cfg_mgr.config.plugins = {"dummy": {"health": True}}
    manager = PluginManager(DIContainer(), cfg_mgr, health_check_interval=1)
    plugin = DummyPlugin()
    manager.load_plugin(plugin)
    assert plugin.load_config == {"health": True}

    health = manager.get_plugin_health()
    assert "dummy" in health
    assert health["dummy"]["health"] == {"healthy": True}
    manager.stop_health_monitor()


def test_load_all_plugins(tmp_path, monkeypatch):
    pkg_dir = tmp_path / "testplugins"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    plugin_module = pkg_dir / "plugin_a.py"
    plugin_module.write_text(
        """
class Plugin:
    class metadata:
        name = 'plug_a'
    def __init__(self):
        self.cfg = None
    def load(self, c, conf):
        self.cfg = conf
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
    return Plugin()
"""
    )
    sys.path.insert(0, str(tmp_path))
    try:
        cfg_mgr = ConfigManager()
        cfg_mgr.config.plugins = {"plug_a": {"test": 1}}
        manager = PluginManager(DIContainer(), cfg_mgr, package="testplugins", health_check_interval=1)
        plugins = manager.load_all_plugins()
        assert len(plugins) == 1
        assert "plug_a" in manager.plugins
        assert plugins[0].cfg == {"test": 1}
    finally:
        sys.path.remove(str(tmp_path))
        manager.stop_health_monitor()
