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


def _lazy_get_service(name: str):
    """Import ``get_service`` lazily to avoid early registry imports."""
    from services.registry import get_service
    return get_service(name)

logger = logging.getLogger(__name__)

# Resolve optional database manager via registry
DatabaseManager = _lazy_get_service("DatabaseManager")
DatabaseConnection = _lazy_get_service("DatabaseConnection")
MockConnection = _lazy_get_service("MockConnection")
EnhancedPostgreSQLManager = _lazy_get_service("EnhancedPostgreSQLManager")
DATABASE_MANAGER_AVAILABLE = DatabaseManager is not None

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
    "EnhancedPostgreSQLManager",
    "DatabaseConnectionPool",
    "ConnectionRetryManager",
    "RetryConfig",
    "UnicodeQueryHandler",
    "UnicodeSQLProcessor",
    "DatabaseError",
    "ConnectionRetryExhausted",
    "ConnectionValidationFailed",
    "UnicodeEncodingError",
    "DatabaseManager",
    "DatabaseConnection",
    "MockConnection",
    "DATABASE_MANAGER_AVAILABLE",
    "dynamic_config",
    "DynamicConfigManager",
    "SecurityConstants",
    "PerformanceConstants",
    "CSSConstants",
]
