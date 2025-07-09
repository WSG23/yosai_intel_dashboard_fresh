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
    DatabaseConfig,
    SecurityConfig,
    get_app_config,
    get_database_config,
    get_security_config,
)
from .config_manager import ConfigManager, get_config, reload_config
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
from .protocols import ConnectionRetryManagerProtocol, RetryConfigProtocol
from .unicode_handler import UnicodeQueryHandler
from .unicode_sql_processor import UnicodeSQLProcessor
from .unicode_processor import (
    QueryUnicodeHandler,
    FileUnicodeHandler,
    UnicodeSecurityValidator,
)


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


def create_config_manager(
    *,
    container: "ServiceContainer | None" = None,
    config_path: str | None = None,
) -> ConfigManager:
    """Factory that wires core config components."""

    if container is not None:
        loader = (
            container.get("config_loader") if container.has("config_loader") else None
        )
        validator = (
            container.get("config_validator")
            if container.has("config_validator")
            else None
        )
        transformer = (
            container.get("config_transformer")
            if container.has("config_transformer")
            else None
        )
    else:  # pragma: no cover - default behaviour
        loader = validator = transformer = None

    loader = loader or ConfigLoader(config_path)
    validator = validator or ConfigValidator()
    transformer = transformer or ConfigTransformer()

    return ConfigManager(
        config_path=config_path,
        loader=loader,
        validator=validator,
        transformer=transformer,
    )


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
    "QueryUnicodeHandler",
    "FileUnicodeHandler",
    "UnicodeSecurityValidator",
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
    "ConfigLoader",
    "ConfigTransformer",
    "ConfigValidator",
    "create_config_manager",
]
