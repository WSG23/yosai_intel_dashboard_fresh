"""Simple registry for optional services."""
from importlib import import_module
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class ServiceRegistry:
    """Registry mapping service names to import paths."""

    def __init__(self) -> None:
        self._services: Dict[str, str] = {}

    def register_service(self, name: str, import_path: str) -> None:
        """Register a service by import path.

        ``import_path`` may include an attribute name using the ``module:attr``
        syntax.
        """
        self._services[name] = import_path

    def get_service(self, name: str) -> Optional[Any]:
        """Return the resolved service or ``None`` if not available."""
        path = self._services.get(name)
        if not path:
            return None
        module_path, _, attr = path.partition(":")
        try:
            module = import_module(module_path)
        except ImportError as exc:  # pragma: no cover - optional dependency
            logger.warning("Optional service '%s' unavailable: %s", name, exc)
            return None
        return getattr(module, attr) if attr else module


# Global registry instance
registry = ServiceRegistry()

# Convenience wrappers
register_service = registry.register_service
get_service = registry.get_service


# Register built-in optional services
register_service("FileProcessor", "services.file_processor:FileProcessor")
register_service("get_analytics_service", "services.analytics_service:get_analytics_service")
register_service("create_analytics_service", "services.analytics_service:create_analytics_service")
register_service("AnalyticsService", "services.analytics_service:AnalyticsService")
