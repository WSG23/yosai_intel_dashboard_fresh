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

    def load(self, container, config):
        self.loaded = True
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
    manager = PluginManager(DIContainer(), ConfigManager(), health_check_interval=1)
    plugin = DummyPlugin()
    result = manager.load_plugin(plugin)

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
    manager = PluginManager(DIContainer(), ConfigManager(), health_check_interval=1)
    plugin = DummyPlugin()
    manager.load_plugin(plugin)

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
    def load(self, c, conf):
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
        manager = PluginManager(DIContainer(), ConfigManager(), package="testplugins", health_check_interval=1)
        plugins = manager.load_all_plugins()
        assert len(plugins) == 1
        assert "plug_a" in manager.plugins
    finally:
        sys.path.remove(str(tmp_path))
        manager.stop_health_monitor()


def test_stop_all_plugins_calls_stop():
    manager = PluginManager(DIContainer(), ConfigManager(), health_check_interval=1)
    plugin = DummyPlugin()
    manager.load_plugin(plugin)

    assert plugin.started
    manager.stop_all_plugins()

    assert not plugin.started
    assert manager.plugin_status["dummy"] == PluginStatus.STOPPED
    manager.stop_health_monitor()


class FailingStopPlugin(DummyPlugin):
    class metadata:
        name = "failstop"

    def stop(self):  # pragma: no cover - error path checked
        raise RuntimeError("boom")


def test_stop_all_plugins_handles_errors():
    manager = PluginManager(DIContainer(), ConfigManager(), health_check_interval=1)
    plugin = FailingStopPlugin()
    manager.load_plugin(plugin)

    manager.stop_all_plugins()

    assert manager.plugin_status["failstop"] == PluginStatus.FAILED
    manager.stop_health_monitor()
