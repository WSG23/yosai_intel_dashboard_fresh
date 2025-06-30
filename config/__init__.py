#!/usr/bin/env python3
"""
Simplified configuration package - Fixed imports
"""

# Import the main configuration system
from .config import (
    Config,
    AppConfig,
    DatabaseConfig,
    SecurityConfig,
    ConfigManager,
    get_config,
    reload_config,
    get_app_config,
    get_database_config, 
    get_security_config
)
from .connection_pool import DatabaseConnectionPool
from .connection_retry import ConnectionRetryManager, RetryConfig
from .unicode_handler import UnicodeQueryHandler
from .database_exceptions import DatabaseError, ConnectionRetryExhausted, ConnectionValidationFailed, UnicodeEncodingError

# Import dynamic configuration helpers
from .dynamic_config import dynamic_config, DynamicConfigManager
from .constants import SecurityConstants, PerformanceConstants, CSSConstants
import logging
from services.registry import get_service

logger = logging.getLogger(__name__)

# Resolve optional database manager via registry
DatabaseManager = get_service("DatabaseManager")
DatabaseConnection = get_service("DatabaseConnection")
MockConnection = get_service("MockConnection")
EnhancedPostgreSQLManager = get_service("EnhancedPostgreSQLManager")
DATABASE_MANAGER_AVAILABLE = DatabaseManager is not None

__all__ = [
    'Config',
    'AppConfig',
    'DatabaseConfig', 
    'SecurityConfig',
    'ConfigManager',
    'get_config',
    'reload_config',
    'get_app_config',
    'get_database_config',
    'get_security_config',
    'EnhancedPostgreSQLManager',
    'DatabaseConnectionPool',
    'ConnectionRetryManager',
    'RetryConfig',
    'UnicodeQueryHandler',
    'DatabaseError',
    'ConnectionRetryExhausted',
    'ConnectionValidationFailed',
    'UnicodeEncodingError',
    'DatabaseManager',
    'DatabaseConnection',
    'MockConnection',
    'DATABASE_MANAGER_AVAILABLE',
    'dynamic_config',
    'DynamicConfigManager',
    'SecurityConstants',
    'PerformanceConstants',
    'CSSConstants'
]
