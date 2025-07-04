from __future__ import annotations

"""Simple plugin registry wrapper exposing health checks automatically."""

from typing import Optional, List, Dict, Any
import logging

from flask import Flask

from core.plugins.manager import PluginManager
from core.container import Container as DIContainer
from config.config import ConfigManager
from core.plugins.protocols import PluginProtocol

logger = logging.getLogger(__name__)


class UnifiedPluginRegistry:
    """Manage plugins and automatically expose health endpoints."""

    def __init__(
        self,
        server: Flask,
        container: Optional[DIContainer] = None,
        config_manager: Optional[ConfigManager] = None,
    ) -> None:
        self.server = server
        self.container = container or DIContainer()
        self.config_manager = config_manager or ConfigManager()
        self.manager = PluginManager(self.container, self.config_manager)
        self._health_registered = False

    # ------------------------------------------------------------------
    def register_plugin(self, plugin: PluginProtocol) -> bool:
        """Load a plugin and expose health endpoint if needed."""
        success = self.manager.load_plugin(plugin)
        if success and not self._health_registered:
            try:
                self.manager.register_health_endpoint(self.server)
                self._health_registered = True
            except Exception as exc:  # pragma: no cover - defensive
                logger.error("Failed to register plugin health endpoint: %s", exc)
        return success

    # ------------------------------------------------------------------
    def register_plugins(self, plugins: List[PluginProtocol]) -> List[bool]:
        """Convenience wrapper to register multiple plugins."""
        return [self.register_plugin(p) for p in plugins]

    # ------------------------------------------------------------------
    def get_health(self) -> Dict[str, Any]:
        """Return current health snapshot for all plugins."""
        return self.manager.get_plugin_health()

    # ------------------------------------------------------------------
    def shutdown(self) -> None:
        """Stop plugins and monitoring."""
        self.manager.stop_all_plugins()
        self.manager.stop_health_monitor()
