from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, cast

if TYPE_CHECKING:  # pragma: no cover - imported for type checking only
    from dash import Dash

from yosai_intel_dashboard.src.core.plugins.auto_config import PluginAutoConfiguration
from yosai_intel_dashboard.src.infrastructure.di.service_container import ServiceContainer


def _initialize_plugins(
    app: Dash,
    config_manager: Any,
    *,
    container: Optional[Any] = None,
    plugin_auto_cls: type[PluginAutoConfiguration] = PluginAutoConfiguration,
) -> None:
    """Initialize plugin system and register shutdown handlers."""
    container = container or ServiceContainer()
    plugin_auto = plugin_auto_cls(
        app, container=container, config_manager=config_manager
    )
    plugin_auto.scan_and_configure("plugins")
    plugin_auto.generate_health_endpoints()
    registry = plugin_auto.registry
    cast(Any, app)._yosai_plugin_manager = registry.plugin_manager

    @app.server.teardown_appcontext  # type: ignore[attr-defined]
    def _shutdown_plugin_manager(exc=None):
        registry.plugin_manager.stop_all_plugins()
        registry.plugin_manager.stop_health_monitor()


__all__ = ["_initialize_plugins"]
