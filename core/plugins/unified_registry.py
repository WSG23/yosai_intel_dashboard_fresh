from __future__ import annotations

from typing import Any, List, Optional
import logging

from dash import Dash

from core.unified_callback_coordinator import UnifiedCallbackCoordinator
from core.callback_manager import CallbackManager
from core.plugins.manager import PluginManager
from core.plugins.protocols import PluginProtocol
from core.container import Container as DIContainer
from config.config import ConfigManager
from services.registry import registry as service_registry

logger = logging.getLogger(__name__)


class UnifiedPluginRegistry:
    """Central registry consolidating plugin management and callbacks."""

    def __init__(
        self,
        app: Dash,
        container: DIContainer,
        config_manager: ConfigManager,
        package: str = "plugins",
        callback_manager: Optional[CallbackManager] = None,
    ) -> None:
        self.app = app
        self.container = container
        self.callback_manager = callback_manager or CallbackManager()
        self.coordinator = UnifiedCallbackCoordinator(app)
        self.plugin_manager = PluginManager(container, config_manager, package=package)
        # Register health endpoint immediately
        try:
            self.plugin_manager.register_health_endpoint(app)
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Failed to register plugin health endpoint: %s", exc)

    # ------------------------------------------------------------------
    def register_plugin(self, plugin: PluginProtocol) -> bool:
        """Load and start a plugin through :class:`PluginManager`."""
        return self.plugin_manager.load_plugin(plugin)

    # ------------------------------------------------------------------
    def get_plugin_service(self, name: str) -> Any:
        """Retrieve a service registered by plugins or optional services."""
        if self.container.has(name):
            return self.container.get(name)
        return service_registry.get_service(name)

    # ------------------------------------------------------------------
    def auto_configure_callbacks(self) -> List[Any]:
        """Register callbacks for all loaded plugins and update health."""
        return self.plugin_manager.register_plugin_callbacks(self.app, self.coordinator)

    # ------------------------------------------------------------------
    def get_plugin_health(self) -> dict:
        """Proxy for :meth:`PluginManager.get_plugin_health`."""
        return self.plugin_manager.get_plugin_health()
