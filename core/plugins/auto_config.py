"""Utility helpers for automatic plugin setup."""
from __future__ import annotations

from typing import Optional, Dict, Any, Callable, List

from dash import Dash

from core.container import Container as DIContainer
from config.config import ConfigManager

from .unified_registry import UnifiedPluginRegistry


class PluginAutoConfiguration:
    """Helper class used to automatically configure plugins."""

    def __init__(
        self,
        app: Dash,
        *,
        container: Optional[DIContainer] = None,
        config_manager: Optional[ConfigManager] = None,
        package: str = "plugins",
    ) -> None:
        self.app = app
        self.container = container or DIContainer()
        self.config_manager = config_manager or ConfigManager()
        self.package = package
        self.registry = UnifiedPluginRegistry(
            app,
            self.container,
            self.config_manager,
            package=package,
        )

    # ------------------------------------------------------------------
    def scan_and_configure(self, plugins_dir: str | None = None) -> Dict[str, Any]:
        """Scan ``plugins_dir`` for plugins, load them and register callbacks."""

        if plugins_dir:
            self.registry.plugin_manager.package = plugins_dir

        self.registry.plugin_manager.load_all_plugins()
        self.registry.auto_configure_callbacks()
        return self.registry.get_plugin_health()

    # ------------------------------------------------------------------
    def validate_plugin_dependencies(self) -> List[str]:
        """Return list of missing dependencies for loaded plugins."""

        missing: List[str] = []
        loaded = set(self.registry.plugin_manager.plugins.keys())
        for name, plugin in self.registry.plugin_manager.plugins.items():
            deps = getattr(getattr(plugin, "metadata", None), "dependencies", []) or []
            for dep in deps:
                if dep not in loaded:
                    missing.append(f"{name}:{dep}")
        return missing

    # ------------------------------------------------------------------
    def generate_health_endpoints(self) -> Dict[str, Callable]:
        """Register health endpoints and return mapping of route -> handler."""

        server = self.app.server if hasattr(self.app, "server") else self.app
        for rule in server.url_map.iter_rules():
            if rule.rule == "/health/plugins":
                func = server.view_functions.get(rule.endpoint)
                if func:
                    return {"/health/plugins": func}

        def plugin_health() -> Any:  # type: ignore[override]
            return self.registry.get_plugin_health()

        server.add_url_rule(
            "/health/plugins",
            "plugin_health",
            plugin_health,
            methods=["GET"],
        )
        return {"/health/plugins": plugin_health}


def setup_plugins(
    app: Dash,
    *,
    container: Optional[DIContainer] = None,
    config_manager: Optional[ConfigManager] = None,
    package: str = "plugins",
) -> UnifiedPluginRegistry:
    """Create a :class:`UnifiedPluginRegistry` and load all plugins."""
    auto = PluginAutoConfiguration(
        app,
        container=container,
        config_manager=config_manager,
        package=package,
    )
    auto.scan_and_configure(package)
    auto.generate_health_endpoints()
    return auto.registry
