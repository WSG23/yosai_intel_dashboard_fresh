"""Minimal plugin config compatibility"""

# Re-export from unified configuration for compatibility
try:
    from config.database_manager import DatabaseManager
    from config.unified_config import (
        UnifiedConfig,
        get_config,
    )

    def get_service_locator():
        """Return configuration object for plugins"""
        return get_config()

    __all__ = [
        "UnifiedConfig",
        "get_config",
        "get_service_locator",
        "DatabaseManager",
    ]

except Exception:

    def get_service_locator():  # pragma: no cover - fallback
        return None

    __all__ = ["get_service_locator"]
