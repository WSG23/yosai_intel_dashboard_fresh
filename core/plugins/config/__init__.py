"""Minimal plugin config compatibility"""

# Re-export from unified configuration for compatibility
try:
    from config.database_manager import DatabaseManager
    from config.unified_config import (
        UnifiedConfig,
        get_config,
    )


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
