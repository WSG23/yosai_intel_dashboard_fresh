"""Optional service accessors for integration with the service registry."""

from __future__ import annotations

from services.registry import get_service

__all__ = [
    "get_database_manager",
    "get_database_connection",
    "get_mock_connection",
    "get_enhanced_postgresql_manager",
]


def _get_service(name: str):
    """Safely retrieve optional services from registry."""
    return get_service(name)


def get_database_manager():
    """Return the optional ``DatabaseManager`` service."""
    return _get_service("DatabaseManager")


def get_database_connection():
    """Return the optional ``DatabaseConnection`` service."""
    return _get_service("DatabaseConnection")


def get_mock_connection():
    """Return the optional ``MockConnection`` service."""
    return _get_service("MockConnection")


def get_enhanced_postgresql_manager():
    """Return the optional ``EnhancedPostgreSQLManager`` service."""
    return _get_service("EnhancedPostgreSQLManager")
