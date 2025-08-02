import sys

from config import create_config_manager
from yosai_intel_dashboard.src.core.plugins.manager import ThreadSafePluginManager as PluginManager
from yosai_intel_dashboard.src.infrastructure.di.service_container import ServiceContainer


class MyPlugin:
    class metadata:
        name = "test_plugin"
        version = "0.1"
        description = "desc"
        author = "tester"

    def __init__(self):
        self.started = False

    def load(self, container, config):
        container.register("service_from_plugin", object())
        return True

    def configure(self, config):
        return True

    def start(self):
        self.started = True
        return True

    def stop(self):
        return True

    def health_check(self):
        return {"healthy": True}


def create_package(tmp_path):
    pkg_dir = tmp_path / "pm_plugins"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    plugin_module = pkg_dir / "plug.py"
    plugin_module.write_text(
        """
from tests.plugins.test_plugin_manager_load_all import MyPlugin

def create_plugin():
    return MyPlugin()
"""
    )
    return pkg_dir


def test_load_all_plugins_registers_services(tmp_path):
    pkg_dir = create_package(tmp_path)
    sys.path.insert(0, str(tmp_path))
    try:
        cfg = create_config_manager()
        cfg.config.plugin_settings["test_plugin"] = {"enabled": True}
        manager = PluginManager(
            ServiceContainer(),
            cfg,
            package="pm_plugins",
            health_check_interval=1,
        )
        plugins = manager.load_all_plugins()
        assert len(plugins) == 1
        assert manager.container.has("service_from_plugin")
        assert plugins[0].started
        health = manager.get_plugin_health()
        assert health["test_plugin"]["health"]["healthy"] is True
    finally:
        sys.path.remove(str(tmp_path))
        manager.stop_health_monitor()
