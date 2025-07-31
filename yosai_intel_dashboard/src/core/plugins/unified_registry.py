from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, List, Optional

from dash import Dash

from config import ConfigManager
from yosai_intel_dashboard.src.infrastructure.callbacks.unified_callbacks import TrulyUnifiedCallbacks
from core.plugins.manager import ThreadSafePluginManager
from core.protocols.plugin import PluginProtocol
from yosai_intel_dashboard.src.infrastructure.di.service_container import ServiceContainer
from services.registry import registry as service_registry

if TYPE_CHECKING:  # pragma: no cover - only for type hints
    from yosai_intel_dashboard.src.infrastructure.callbacks.unified_callbacks import TrulyUnifiedCallbacks

logger = logging.getLogger(__name__)


class UnifiedPluginRegistry:
    """Central registry consolidating plugin management and callbacks."""

    def __init__(
        self,
        app: Dash,
        container: ServiceContainer,
        config_manager: ConfigManager,
        package: str = "plugins",
        callback_manager: Optional[TrulyUnifiedCallbacks] = None,
    ) -> None:
        self.app = app
        self.container = container
        self.callback_manager = callback_manager or TrulyUnifiedCallbacks()

        # Import lazily to avoid circular dependency during module import
        from yosai_intel_dashboard.src.infrastructure.callbacks.unified_callbacks import TrulyUnifiedCallbacks

        self.coordinator = TrulyUnifiedCallbacks(app)
        self.plugin_manager = ThreadSafePluginManager(
            container, config_manager, package=package
        )
        # Register health endpoint immediately
        try:
            self.plugin_manager.register_health_endpoint(app)
        except Exception as exc:  # pragma: no cover - defensive
            logger.error(f"Failed to register plugin health endpoint: {exc}")

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
