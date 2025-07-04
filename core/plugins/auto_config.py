"""Utility helpers for automatic plugin setup."""
from __future__ import annotations

from typing import Optional

from dash import Dash

from core.container import Container as DIContainer
from config.config import ConfigManager

from .unified_registry import UnifiedPluginRegistry


def setup_plugins(
    app: Dash,
    *,
    container: Optional[DIContainer] = None,
    config_manager: Optional[ConfigManager] = None,
    package: str = "plugins",
) -> UnifiedPluginRegistry:
    """Create a :class:`UnifiedPluginRegistry` and load all plugins."""
    container = container or DIContainer()
    config_manager = config_manager or ConfigManager()

    registry = UnifiedPluginRegistry(
        app,
        container,
        config_manager,
        package=package,
    )
    registry.plugin_manager.load_all_plugins()
    registry.auto_configure_callbacks()
    return registry
