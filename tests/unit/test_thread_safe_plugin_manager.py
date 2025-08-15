from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor

from yosai_intel_dashboard.src.core.plugins.manager import ThreadSafePluginManager
from yosai_intel_dashboard.src.core.protocols.plugin import PluginMetadata
from yosai_intel_dashboard.src.infrastructure.config import create_config_manager
from yosai_intel_dashboard.src.infrastructure.di.service_container import (
    ServiceContainer,
)


class ConcurrencyPlugin:
    metadata = PluginMetadata(
        name="concurrent",
        version="0.1",
        description="concurrency test",
        author="tester",
    )

    def __init__(self):
        self.start_count = 0

    def load(self, container, config):
        return True

    def configure(self, config):
        return True

    def start(self):
        self.start_count += 1
        return True

    def stop(self):
        return True

    def health_check(self):
        return {"healthy": True}


def test_concurrent_load_plugin():
    cfg = create_config_manager()
    cfg.config.plugin_settings["concurrent"] = {"enabled": True}
    manager = ThreadSafePluginManager(
        ServiceContainer(), cfg, health_check_interval=0.1
    )
    plugin = ConcurrencyPlugin()

    with ThreadPoolExecutor(max_workers=5) as exe:
        futures = [exe.submit(manager.load_plugin, plugin) for _ in range(5)]
        results = [f.result() for f in futures]

    assert results.count(True) == 1
    assert plugin.start_count == 1
    manager.stop_health_monitor()


def test_concurrent_health_checks():
    cfg = create_config_manager()
    cfg.config.plugin_settings["concurrent"] = {"enabled": True}
    manager = ThreadSafePluginManager(
        ServiceContainer(), cfg, health_check_interval=0.1
    )
    plugin = ConcurrencyPlugin()
    manager.load_plugin(plugin)

    time.sleep(0.3)

    with ThreadPoolExecutor(max_workers=5) as exe:
        futures = [exe.submit(manager.get_plugin_health) for _ in range(10)]
        results = [f.result() for f in futures]

    for res in results:
        assert res["concurrent"]["health"]["healthy"] is True

    assert manager.health_snapshot["concurrent"]["health"]["healthy"] is True
    manager.stop_health_monitor()
