"""Lightweight service registry for application-wide singletons."""

from __future__ import annotations

from typing import Any, Dict, Optional, TypeVar

T = TypeVar("T")


class ServiceRegistry:
    """Minimal registry to manage shared service instances."""

    _services: Dict[str, Any] = {}

    @classmethod
    def register(cls, name: str, service: Any) -> None:
        """Register ``service`` under ``name`` overwriting existing entry."""

        cls._services[name] = service

    @classmethod
    def get(cls, name: str, default: Optional[T] = None) -> T:
        """Return service registered under ``name`` or ``default`` if absent."""

        return cls._services.get(name, default)  # type: ignore[return-value]

    @classmethod
    def remove(cls, name: str) -> None:
        """Remove ``name`` from registry if present."""

        cls._services.pop(name, None)


# Backwards compatibility: provide module-level ``registry`` alias so external
# code can import ``from ...core import ServiceRegistry, registry`` and continue
# using ``registry.register(...)`` style APIs.
registry = ServiceRegistry

__all__ = ["ServiceRegistry", "registry"]
