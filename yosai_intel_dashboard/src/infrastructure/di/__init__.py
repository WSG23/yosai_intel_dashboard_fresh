"""Application-wide dependency injection container utilities."""
from __future__ import annotations

from typing import Any, Callable, Optional

from .service_container import (
    CircularDependencyError,
    DependencyInjectionError,
    ServiceContainer,
    ServiceLifetime,
)


def get_settings() -> Any:
    """Load configuration settings.

    Falls back to a minimal object with required accessors if the full
    configuration system cannot be loaded (for example when optional
    dependencies are missing during tests).
    """
    try:  # pragma: no cover - best effort
        from ..config import get_config

        return get_config()
    except Exception:  # pragma: no cover - defensive fallback
        class _Fallback:
            def get_database_config(self) -> dict:  # type: ignore[return-value]
                return {}

            def get_analytics_config(self) -> dict:  # type: ignore[return-value]
                return {}

        return _Fallback()


# Global container instance -------------------------------------------------
container = ServiceContainer()
_settings = get_settings()

# Pre-register common configuration lookups
container.register_singleton("config", _settings)
container.register_transient(
    "database_config", object, factory=lambda _c: _settings.get_database_config()
)
container.register_transient(
    "analytics_config", object, factory=lambda _c: _settings.get_analytics_config()
)


def register_singleton(
    key: str,
    implementation: Any,
    *,
    protocol: Optional[type] = None,
) -> ServiceContainer:
    """Convenience wrapper to register a singleton service."""
    return container.register_singleton(key, implementation, protocol=protocol)


def register_factory(
    key: str,
    factory: Callable[[ServiceContainer], Any],
    *,
    protocol: Optional[type] = None,
) -> ServiceContainer:
    """Register a factory that creates a new instance on each resolution."""
    return container.register_transient(key, object, protocol=protocol, factory=factory)


def configure_database(
    factory: Callable[[ServiceContainer], Any]
) -> ServiceContainer:
    """Helper to register the database service factory."""
    return register_factory("database_service", factory)


def configure_analytics(
    factory: Callable[[ServiceContainer], Any]
) -> ServiceContainer:
    """Helper to register the analytics service factory."""
    return register_factory("analytics_service", factory)


__all__ = [
    "container",
    "register_singleton",
    "register_factory",
    "configure_database",
    "configure_analytics",
    "get_settings",
    # Re-export core classes for backward compatibility
    "ServiceContainer",
    "ServiceLifetime",
    "DependencyInjectionError",
    "CircularDependencyError",
]
