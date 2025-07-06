"""Minimal plugin config compatibility"""

# Import configuration manager from the new configuration module

from config.config import ConfigManager, get_config
from config.database_manager import DatabaseManager

def get_service_locator() -> ConfigManager:
    """Return configuration object for plugins"""

    return get_config()

__all__ = [
    "ConfigManager",
    "get_config",
    "get_service_locator",
    "DatabaseManager",
]
