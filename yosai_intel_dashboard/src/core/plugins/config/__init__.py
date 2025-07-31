"""Minimal plugin config compatibility"""

# Re-export from unified configuration for compatibility
from config import ConfigManager, get_config
from yosai_intel_dashboard.src.infrastructure.config.database_manager import DatabaseManager


def get_service_locator() -> ConfigManager:
    """Return configuration object for plugins"""

    return get_config()


__all__ = [
    "ConfigManager",
    "get_config",
    "get_service_locator",
    "DatabaseManager",
]
