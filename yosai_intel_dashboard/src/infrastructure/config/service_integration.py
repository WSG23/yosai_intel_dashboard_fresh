"""Optional service accessors for integration with the service registry."""

from __future__ import annotations

from yosai_intel_dashboard.src.core.container import container

# Lazy import to avoid circular dependencies during module import
def get_service_registry():
    """Return the global optional service registry."""
    from yosai_intel_dashboard.src.core.registry import registry

    return registry

__all__ = ["get_database_connection_factory"]


def _get_service(name: str):
    """Safely retrieve optional services from the container."""
    if container.has(name):
        return container.get(name)
    return None


def get_database_connection_factory():
    """Return the optional ``DatabaseConnectionFactory`` service."""
    return _get_service("DatabaseConnectionFactory")
