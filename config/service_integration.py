"""Optional service accessors for integration with the service registry."""

from __future__ import annotations

from core.service_container import ServiceContainer
from database.types import DatabaseConnection
from .protocols import (
    DatabaseManagerProtocol,
    EnhancedPostgreSQLManagerProtocol,
)

__all__ = [
    "get_database_manager",
    "get_database_connection",
    "get_mock_connection",
    "get_enhanced_postgresql_manager",
]


def _get_container(
    container: ServiceContainer | None = None,
) -> ServiceContainer | None:
    if container is not None:
        return container
    try:  # pragma: no cover - dash may be missing in tests
        from dash import get_app

        app = get_app()
        return getattr(app, "_service_container", None)
    except Exception:
        return None


def get_database_manager(
    container: ServiceContainer | None = None,
) -> DatabaseManagerProtocol | None:
    """Return the optional ``DatabaseManager`` service."""
    c = _get_container(container)
    if c and c.has("database_manager"):
        return c.get("database_manager")
    return None


def get_database_connection(
    container: ServiceContainer | None = None,
) -> DatabaseConnection | None:
    """Return the optional ``DatabaseConnection`` service."""
    c = _get_container(container)
    if c and c.has("database_connection"):
        return c.get("database_connection")
    manager = get_database_manager(c)
    return manager.get_connection() if manager else None


def get_mock_connection(
    container: ServiceContainer | None = None,
) -> DatabaseConnection | None:
    """Return the optional ``MockConnection`` service."""
    c = _get_container(container)
    if c and c.has("mock_connection"):
        return c.get("mock_connection")
    return None


def get_enhanced_postgresql_manager(
    container: ServiceContainer | None = None,
) -> EnhancedPostgreSQLManagerProtocol | None:
    """Return the optional ``EnhancedPostgreSQLManager`` service."""
    c = _get_container(container)
    if c and c.has("enhanced_postgresql_manager"):
        return c.get("enhanced_postgresql_manager")
    return None
