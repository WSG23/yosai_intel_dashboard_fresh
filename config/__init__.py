#!/usr/bin/env python3
"""
Simplified configuration package - Fixed imports
"""

import logging

# Import the main configuration system
from core.protocols import ConfigProviderProtocol

from .config import (
    AppConfig,
    Config,
    ConfigManager,
    DatabaseConfig,
    SecurityConfig,
    get_app_config,
    get_config,
    get_database_config,
    get_security_config,
    reload_config,
)
from .connection_pool import DatabaseConnectionPool
from .connection_retry import ConnectionRetryManager, RetryConfig
from .protocols import ConnectionRetryManagerProtocol, RetryConfigProtocol
from .constants import CSSConstants, PerformanceConstants, SecurityConstants
from .database_exceptions import (
    ConnectionRetryExhausted,
    ConnectionValidationFailed,
    DatabaseError,
    UnicodeEncodingError,
)

# Import dynamic configuration helpers
from .dynamic_config import DynamicConfigManager, dynamic_config
from .unicode_handler import UnicodeQueryHandler
from .unicode_sql_processor import UnicodeSQLProcessor


def _get_service(name: str):
    """Retrieve a service from :mod:`services.registry` on demand."""
    from services.registry import get_service

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


logger = logging.getLogger(__name__)

__all__ = [
    "Config",
    "AppConfig",
    "DatabaseConfig",
    "SecurityConfig",
    "ConfigManager",
    "ConfigProviderProtocol",
    "get_config",
    "reload_config",
    "get_app_config",
    "get_database_config",
    "get_security_config",
    "get_enhanced_postgresql_manager",
    "DatabaseConnectionPool",
    "ConnectionRetryManager",
    "RetryConfig",
    "ConnectionRetryManagerProtocol",
    "RetryConfigProtocol",
    "UnicodeQueryHandler",
    "UnicodeSQLProcessor",
    "DatabaseError",
    "ConnectionRetryExhausted",
    "ConnectionValidationFailed",
    "UnicodeEncodingError",
    "get_database_manager",
    "get_database_connection",
    "get_mock_connection",
    "dynamic_config",
    "DynamicConfigManager",
    "SecurityConstants",
    "PerformanceConstants",
    "CSSConstants",
]
