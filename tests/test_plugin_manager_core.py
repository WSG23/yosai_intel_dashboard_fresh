from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path

from config import create_config_manager
from core.plugins.manager import ThreadSafePluginManager as PluginManager
from core.protocols.plugin import PluginMetadata, PluginStatus
from yosai_intel_dashboard.src.infrastructure.di.service_container import ServiceContainer


class DummyPlugin:
    """Simple plugin for testing"""

    metadata = PluginMetadata(
        name="dummy",
        version="0.1",
        description="dummy plugin",
        author="tester",
    )

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

    metadata = PluginMetadata(
        name="nohealth",
        version="0.1",
        description="no health plugin",
        author="tester",
    )

    def load(self, container, config):
        return True

    def configure(self, config):
        return True

    def start(self):
        return True

    def stop(self):
        return True


def test_load_plugin_success(tmp_path):
    cfg = create_config_manager()
    cfg.config.plugin_settings["dummy"] = {"enabled": True}
    manager = PluginManager(ServiceContainer(), cfg, health_check_interval=1)
    plugin = DummyPlugin()
    result = manager.load_plugin(plugin)

    assert result is True
    assert plugin.started
    assert "dummy" in manager.plugins
    assert manager.plugin_status["dummy"] == PluginStatus.STARTED
    manager.stop_health_monitor()


def test_load_plugin_failure_missing_health():
    cfg = create_config_manager()
    cfg.config.plugin_settings["nohealth"] = {"enabled": True}
    manager = PluginManager(ServiceContainer(), cfg, health_check_interval=1)
    plugin = NoHealthPlugin()
    result = manager.load_plugin(plugin)

    assert result is False
    assert manager.plugin_status["nohealth"] == PluginStatus.FAILED
    manager.stop_health_monitor()


def test_get_plugin_health(monkeypatch):
    cfg = create_config_manager()
    cfg.config.plugin_settings["dummy"] = {"enabled": True}
    manager = PluginManager(ServiceContainer(), cfg, health_check_interval=1)
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
from core.protocols.plugin import PluginMetadata

class Plugin:
    metadata = PluginMetadata(
        name='plug_a',
        version='0.1',
        description='plug a',
        author='tester',
    )
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
        cfg = create_config_manager()
        cfg.config.plugin_settings["plug_a"] = {"enabled": True}
        manager = PluginManager(
            ServiceContainer(),
            cfg,
            package="testplugins",
            health_check_interval=1,
        )
        plugins = manager.load_all_plugins()
        assert len(plugins) == 1
        assert "plug_a" in manager.plugins
    finally:
        sys.path.remove(str(tmp_path))
        manager.stop_health_monitor()


def test_stop_all_plugins_calls_stop():
    cfg = create_config_manager()
    cfg.config.plugin_settings["dummy"] = {"enabled": True}
    manager = PluginManager(ServiceContainer(), cfg, health_check_interval=1)
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
    cfg = create_config_manager()
    cfg.config.plugin_settings["failstop"] = {"enabled": True}
    manager = PluginManager(ServiceContainer(), cfg, health_check_interval=1)
    plugin = FailingStopPlugin()
    manager.load_plugin(plugin)

    manager.stop_all_plugins()

    assert manager.plugin_status["failstop"] == PluginStatus.FAILED
    manager.stop_health_monitor()
