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

logger = logging.getLogger(__name__)

# Try to import database manager safely
try:
    from .database_manager import DatabaseManager, DatabaseConnection, MockConnection, EnhancedPostgreSQLManager
    DATABASE_MANAGER_AVAILABLE = True
except ImportError as e:
    logger.info(f"Warning: Database manager not available: {e}")
    DatabaseManager = None
    DatabaseConnection = None 
    MockConnection = None
    DATABASE_MANAGER_AVAILABLE = False

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
