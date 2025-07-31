import logging

from .decorators import safe_callback

logger = logging.getLogger(__name__)

try:
    from .auto_config import PluginAutoConfiguration
    from .manager import ThreadSafePluginManager as PluginManager
    from .performance_manager import EnhancedThreadSafePluginManager

    PLUGINS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Plugin system not available: {e}")
    PLUGINS_AVAILABLE = False

    class PluginManager:
        """Minimal stub used when plugin dependencies are missing."""

        def __init__(self, *args, **kwargs) -> None:  # pragma: no cover - simple stub
            pass

        def discover_plugins(self):
            return []

        def load_plugin(self, plugin):
            return False

    class PluginAutoConfiguration:
        """No-op auto configuration when plugins are disabled."""

        def __init__(self, *args, **kwargs) -> None:  # pragma: no cover - simple stub
            pass

        def scan_and_configure(self, *args):
            pass


__all__ = [
    "PluginManager",
    "PluginAutoConfiguration",
    "EnhancedThreadSafePluginManager",
    "PLUGINS_AVAILABLE",
    "safe_callback",
]
