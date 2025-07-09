import importlib
import logging
import pkgutil
import threading
import time
from typing import Any, Dict, List

from config import ConfigManager
from core.callback_manager import CallbackManager
from core.service_container import ServiceContainer
from services.data_processing.core.protocols import (
    CallbackPluginProtocol,
    PluginPriority,
    PluginProtocol,
    PluginStatus,
)

from .dependency_resolver import PluginDependencyResolver

logger = logging.getLogger(__name__)


class PluginManager:
    """Simple plugin manager that loads plugins from the 'plugins' package."""

    def __init__(
        self,
        container: ServiceContainer,
        config_manager: ConfigManager,
        package: str = "plugins",
        health_check_interval: int = 60,
    ):
        self.container = container
        self.config_manager = config_manager
        self.package = package
        self._resolver = PluginDependencyResolver()
        self.loaded_plugins: List[Any] = []
        self.plugins: Dict[str, PluginProtocol] = {}
        self.plugin_status: Dict[str, PluginStatus] = {}
        self.health_snapshot: Dict[str, Any] = {}
        self._health_check_interval = health_check_interval
        self._health_monitor_active = True
        self._health_thread = threading.Thread(
            target=self._health_monitor_loop, daemon=True
        )
        self._health_thread.start()

    def __enter__(self):
        """Start the health monitor when entering the context."""
        if not self._health_thread.is_alive():
            self._health_monitor_active = True
            self._health_thread = threading.Thread(
                target=self._health_monitor_loop, daemon=True
            )
            self._health_thread.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        """Ensure the health monitor thread is stopped on exit."""
        self.stop_health_monitor()

    @staticmethod
    def _get_priority(plugin: PluginProtocol) -> int:
        """Return numeric priority value for sorting."""
        try:
            pr = getattr(plugin.metadata, "priority", PluginPriority.NORMAL)
            if isinstance(pr, PluginPriority):
                return pr.value
            return int(pr)
        except Exception:
            return PluginPriority.NORMAL.value

    def load_all_plugins(self) -> List[Any]:
        """Discover and load plugins from ``self.package``."""
        try:
            pkg = importlib.import_module(self.package)
        except ModuleNotFoundError:
            logger.info("Plugins package '%s' not found", self.package)
            return []

        discovered: List[PluginProtocol] = []
        for info in pkgutil.iter_modules(pkg.__path__, prefix=f"{self.package}."):
            if not info.ispkg:
                continue
            module_name = info.name
            try:
                module = importlib.import_module(module_name)
                plugin = None
                if hasattr(module, "create_plugin"):
                    plugin = module.create_plugin()
                elif hasattr(module, "plugin"):
                    plugin = module.plugin
                elif hasattr(module, "init_plugin"):
                    plugin = module.init_plugin(self.container, self.config_manager)
                if plugin:
                    discovered.append(plugin)
                self.loaded_plugins.append(module)
                logger.info("Loaded plugin %s", module_name)
            except Exception as exc:
                logger.error("Failed to load plugin %s: %s", module_name, exc)

        try:
            ordered = self._resolver.resolve(discovered)
        except ValueError as exc:
            if "Circular dependency" in str(exc):
                logger.error("Plugin dependency cycle detected: %s", exc)
                return []
            logger.error("Failed to resolve plugin dependencies: %s", exc)
            return []
        except Exception as exc:
            logger.error("Failed to resolve plugin dependencies: %s", exc)
            return []

        ordered.sort(key=self._get_priority)
        results: List[PluginProtocol] = []
        for plugin in ordered:
            if self.load_plugin(plugin):
                results.append(plugin)
        return results

    def load_plugin(self, plugin: PluginProtocol) -> bool:
        """Load a specific plugin instance"""
        try:
            if hasattr(plugin, "metadata"):
                name = plugin.metadata.name
            else:
                name = plugin.__class__.__name__

            config = self.config_manager.get_plugin_config(name)

            if not callable(getattr(plugin, "health_check", None)):
                logger.error("Plugin %s does not implement health_check", name)
                self.plugin_status[name] = PluginStatus.FAILED
                return False

            success = plugin.load(self.container, config)
            if success:
                try:
                    plugin.configure(config)
                except Exception as exc:
                    logger.error("Failed to configure plugin %s: %s", name, exc)
                    self.plugin_status[name] = PluginStatus.FAILED
                    return False
                plugin.start()
                self.plugins[name] = plugin
                self.plugin_status[name] = PluginStatus.STARTED
                logger.info("Loaded plugin %s", name)
                return True
            self.plugin_status[name] = PluginStatus.FAILED
            return False
        except Exception as exc:
            logger.error(
                "Failed to load plugin %s: %s", getattr(plugin, "metadata", plugin), exc
            )
            return False

    def register_plugin_callbacks(
        self, app: Any, manager: CallbackManager
    ) -> List[Any]:
        """Register callbacks for all loaded plugins"""
        results = []
        try:
            self.register_health_endpoint(app)
        except Exception as exc:  # pragma: no cover - log and continue
            logger.error("Failed to register plugin health endpoint: %s", exc)
        for plugin in self.plugins.values():
            if isinstance(plugin, CallbackPluginProtocol) or hasattr(
                plugin, "register_callbacks"
            ):
                try:
                    result = plugin.register_callbacks(manager, self.container)
                    results.append(result)
                except Exception as exc:  # pragma: no cover - log and continue
                    logger.error("Failed to register callbacks for %s: %s", plugin, exc)
                    results.append(False)
        return results

    def get_plugin_health(self) -> Dict[str, Any]:
        """Return health status for all loaded plugins"""
        health = {}
        for name, plugin in self.plugins.items():
            try:
                plugin_health = plugin.health_check()
            except Exception as exc:
                plugin_health = {"healthy": False, "error": str(exc)}
            health[name] = {
                "health": plugin_health,
                "status": self.plugin_status.get(name),
            }
        return health

    def _health_monitor_loop(self) -> None:
        """Background loop to periodically collect plugin health"""
        while self._health_monitor_active:
            try:
                self.health_snapshot = self.get_plugin_health()
            except Exception as exc:
                logger.error("Health monitoring error: %s", exc)
            time.sleep(self._health_check_interval)

    def stop_health_monitor(self) -> None:
        """Stop the background health monitor thread"""
        self._health_monitor_active = False
        if self._health_thread.is_alive():
            self._health_thread.join(timeout=1)

    def stop_all_plugins(self) -> None:
        """Stop all loaded plugins gracefully."""
        for name, plugin in self.plugins.items():
            try:
                result = plugin.stop()
                if result:
                    self.plugin_status[name] = PluginStatus.STOPPED
                else:
                    self.plugin_status[name] = PluginStatus.FAILED
            except Exception as exc:  # pragma: no cover - defensive
                logger.error("Failed to stop plugin %s: %s", name, exc)
                self.plugin_status[name] = PluginStatus.FAILED

    def register_health_endpoint(self, app: Any) -> None:
        """Expose aggregated plugin health via /health/plugins"""
        server = app.server if hasattr(app, "server") else app

        # Avoid duplicate registration if another component already added it
        for rule in server.url_map.iter_rules():
            if rule.rule == "/health/plugins":
                return

        def plugin_health():
            """Plugin health snapshot.
            ---
            get:
              description: Aggregated plugin health
              responses:
                200:
                  description: Plugin health data
                  content:
                    application/json:
                      schema:
                        type: object
            """
            return self.health_snapshot or self.get_plugin_health()

        server.add_url_rule(
            "/health/plugins",
            "plugin_health",
            plugin_health,
            methods=["GET"],
        )

    def register_performance_endpoint(self, app: Any) -> None:
        """Expose plugin performance metrics via /health/plugins/performance"""
        server = app.server if hasattr(app, "server") else app
        for rule in server.url_map.iter_rules():
            if rule.rule == "/health/plugins/performance":
                return

        def plugin_performance():
            return getattr(app, "_yosai_plugin_manager").get_plugin_performance_metrics()

        server.add_url_rule(
            "/health/plugins/performance",
            "plugin_performance",
            plugin_performance,
            methods=["GET"],
        )


class ThreadSafePluginManager(PluginManager):
    """Plugin manager variant with locking around shared state."""

    def __init__(self, *args, **kwargs) -> None:
        self._lock = threading.RLock()
        super().__init__(*args, **kwargs)

    # ------------------------------------------------------------------
    def load_plugin(self, plugin: PluginProtocol) -> bool:  # type: ignore[override]
        with self._lock:
            if hasattr(plugin, "metadata"):
                name = plugin.metadata.name
            else:
                name = plugin.__class__.__name__
            if name in self.plugins:
                return False
            return super().load_plugin(plugin)

    # ------------------------------------------------------------------
    def load_all_plugins(self) -> List[Any]:  # type: ignore[override]
        with self._lock:
            return super().load_all_plugins()

    # ------------------------------------------------------------------
    def register_plugin_callbacks(
        self, app: Any, manager: CallbackManager
    ) -> List[Any]:  # type: ignore[override]
        with self._lock:
            return super().register_plugin_callbacks(app, manager)

    # ------------------------------------------------------------------
    def get_plugin_health(self) -> Dict[str, Any]:  # type: ignore[override]
        with self._lock:
            return super().get_plugin_health()

    # ------------------------------------------------------------------
    def _health_monitor_loop(self) -> None:  # type: ignore[override]
        while self._health_monitor_active:
            with self._lock:
                try:
                    self.health_snapshot = self.get_plugin_health()
                except Exception as exc:  # pragma: no cover - defensive
                    logger.error("Health monitoring error: %s", exc)
            time.sleep(self._health_check_interval)

    # ------------------------------------------------------------------
    def stop_all_plugins(self) -> None:  # type: ignore[override]
        with self._lock:
            super().stop_all_plugins()
