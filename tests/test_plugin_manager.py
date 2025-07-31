from __future__ import annotations

import sys
import time
from pathlib import Path

from config import create_config_manager
from core.plugins.manager import ThreadSafePluginManager as PluginManager
from core.protocols.plugin import PluginMetadata
from yosai_intel_dashboard.src.infrastructure.di.service_container import ServiceContainer


class SimplePlugin:
    metadata = PluginMetadata(
        name="simple",
        version="0.1",
        description="test plugin",
        author="tester",
    )

    def __init__(self):
        self.started = False

    def load(self, container, config):
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
    cfg = create_config_manager()
    cfg.config.plugin_settings["simple"] = {"enabled": True}
    manager = PluginManager(ServiceContainer(), cfg, health_check_interval=1)
    plugin = SimplePlugin()
    assert manager.load_plugin(plugin) is True
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
from core.protocols.plugin import PluginMetadata

class Plug:
    metadata = PluginMetadata(
        name='auto',
        version='0.1',
        description='auto plugin',
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
    return Plug()
"""
    )
    sys.path.insert(0, str(tmp_path))
    try:
        cfg = create_config_manager()
        cfg.config.plugin_settings["auto"] = {"enabled": True}
        manager = PluginManager(
            ServiceContainer(),
            cfg,
            package="sampleplugins",
            health_check_interval=1,
        )
        plugins = manager.load_all_plugins()
        assert len(plugins) == 1
        assert "auto" in manager.plugins
    finally:
        sys.path.remove(str(tmp_path))
        manager.stop_health_monitor()


def test_get_plugin_health_snapshot():
    cfg = create_config_manager()
    cfg.config.plugin_settings["simple"] = {"enabled": True}
    manager = PluginManager(ServiceContainer(), cfg, health_check_interval=1)
    plugin = SimplePlugin()
    manager.load_plugin(plugin)
    time.sleep(1.2)
    snapshot = manager.health_snapshot
    assert "simple" in snapshot
    assert snapshot["simple"]["health"] == {"healthy": True}
    manager.stop_health_monitor()
