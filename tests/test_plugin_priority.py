from __future__ import annotations

import sys

from config import create_config_manager
from yosai_intel_dashboard.src.core.plugins.manager import ThreadSafePluginManager as PluginManager
from yosai_intel_dashboard.src.core.protocols.plugin import PluginPriority
from yosai_intel_dashboard.src.infrastructure.di.service_container import ServiceContainer


def test_priority_order(tmp_path):
    pkg_dir = tmp_path / "prio_plugins"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")

    plugin_a = pkg_dir / "plugin_a.py"
    plugin_a.write_text(
        """
from yosai_intel_dashboard.src.core.protocols.plugin import PluginPriority
class PluginA:
    class metadata:
        name = 'a'
        priority = PluginPriority.LOW
    def load(self, c, conf): return True
    def configure(self, conf): return True
    def start(self): return True
    def stop(self): return True
    def health_check(self): return {'healthy': True}

def create_plugin():
    return PluginA()
"""
    )

    plugin_b = pkg_dir / "plugin_b.py"
    plugin_b.write_text(
        """
from yosai_intel_dashboard.src.core.protocols.plugin import PluginPriority
class PluginB:
    class metadata:
        name = 'b'
        priority = PluginPriority.CRITICAL
    def load(self, c, conf): return True
    def configure(self, conf): return True
    def start(self): return True
    def stop(self): return True
    def health_check(self): return {'healthy': True}

def create_plugin():
    return PluginB()
"""
    )

    sys.path.insert(0, str(tmp_path))
    try:
        cfg = create_config_manager()
        cfg.config.plugin_settings["a"] = {}
        cfg.config.plugin_settings["b"] = {}
        manager = PluginManager(
            ServiceContainer(),
            cfg,
            package="prio_plugins",
            health_check_interval=1,
        )
        plugins = manager.load_all_plugins()
        names = [p.metadata.name for p in plugins]
        assert names == ["b", "a"]
    finally:
        sys.path.remove(str(tmp_path))
        manager.stop_health_monitor()
