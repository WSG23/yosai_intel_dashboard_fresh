import logging
logger = logging.getLogger(__name__)

try:
    from .manager import ThreadSafePluginManager as PluginManager
    from .performance_manager import EnhancedThreadSafePluginManager
    from .auto_config import PluginAutoConfiguration
    PLUGINS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Plugin system not available: {e}")
    PLUGINS_AVAILABLE = False
    class PluginManager:
        def __init__(self, *args, **kwargs):
            pass
        def discover_plugins(self):
            return []
        def load_plugin(self, plugin):
            return False
    class PluginAutoConfiguration:
        def __init__(self, *args, **kwargs):
            pass
        def scan_and_configure(self, *args):
            pass

__all__ = [
    "PluginManager",
    "PluginAutoConfiguration",
    "EnhancedThreadSafePluginManager",
    "PLUGINS_AVAILABLE",
]
