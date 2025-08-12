from __future__ import annotations

"""Lightweight service registry used for global lookups."""

from typing import Any, Dict


class ServiceRegistry:
    """Very small service registry.

    Services are stored by a string key and can be retrieved or removed later.
    The implementation is intentionally minimal for ease of use in tests and
    runtime modules.
    """

    def __init__(self) -> None:
        self._services: Dict[str, Any] = {}

    def register(self, name: str, service: Any) -> None:
        """Register *service* under *name*."""

        self._services[name] = service

    def get(self, name: str) -> Any:
        """Return the service registered under *name*.

        Raises ``KeyError`` if the service has not been registered.
        """

        return self._services[name]

    def remove(self, name: str) -> None:
        """Remove the service registered under *name* if present."""

        self._services.pop(name, None)


# Global registry instance used across the application
registry = ServiceRegistry()

__all__ = ["ServiceRegistry", "registry"]
