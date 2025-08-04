"""Application service container with built-in configuration services."""

from __future__ import annotations

from typing import Optional, Type, TypeVar

from ..infrastructure.config.settings import get_settings
from ..infrastructure.di.service_container import (
    CircularDependencyError,
    DependencyInjectionError,
    ServiceContainer as _BaseServiceContainer,
    ServiceLifetime,
)

T = TypeVar("T")


class ServiceContainer(_BaseServiceContainer):
    """Service container that lazily exposes configuration objects."""

    def _ensure_builtin(self, service_key: str) -> None:
        """Register built-in services on first request."""
        if service_key == "config" and not self.has("config"):
            self.register("config", get_settings())
        elif service_key == "database_config" and not self.has("database_config"):
            self.register("database_config", get_settings().database)
        elif service_key == "analytics_config" and not self.has("analytics_config"):
            self.register("analytics_config", get_settings().analytics)

    def get(self, service_key: str, protocol_type: Optional[Type[T]] = None) -> T:
        self._ensure_builtin(service_key)
        return super().get(service_key, protocol_type)

    # ------------------------------------------------------------------
    def configure_database(self) -> "ServiceContainer":
        """Create and register database-related services."""
        self._ensure_builtin("database_config")
        return self

    def configure_analytics(self) -> "ServiceContainer":
        """Create and register analytics-related services."""
        self._ensure_builtin("analytics_config")
        return self


__all__ = [
    "ServiceContainer",
    "ServiceLifetime",
    "DependencyInjectionError",
    "CircularDependencyError",
]

