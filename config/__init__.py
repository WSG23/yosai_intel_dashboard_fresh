"""Configuration module with proper imports and error handling."""

import logging
from typing import Any, Dict, Optional

from services.registry import get_service

from .base import (
    AppConfig,
    Config,
    DatabaseConfig,
    SecurityConfig,
)
from .config_loader import ConfigLoader
from .config_transformer import ConfigTransformer
from .config_validator import ConfigValidator, ValidationResult
from .constants import CSSConstants, PerformanceConstants, SecurityConstants
from .dynamic_config import DynamicConfigManager, dynamic_config
from .protocols import (
    ConfigLoaderProtocol,
    ConfigTransformerProtocol,
    ConfigValidatorProtocol,
)


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


def create_config_manager(
    *,
    container: Optional[Any] = None,
    config_path: Optional[str] = None,
) -> ConfigManager:
    """Factory that wires core config components."""
    loader: ConfigLoaderProtocol | None
    validator: ConfigValidatorProtocol | None
    transformer: ConfigTransformerProtocol | None

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
    else:
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


# Convenience functions
def get_app_config() -> AppConfig:
    """Get app configuration"""
    return get_config().get_app_config()


def get_database_config() -> DatabaseConfig:
    """Get database configuration"""
    return get_config().get_database_config()


def get_security_config() -> SecurityConfig:
    """Get security configuration"""
    return get_config().get_security_config()


def get_plugin_config(name: str) -> Dict[str, Any]:
    """Get configuration for a specific plugin"""
    return get_config().get_plugin_config(name)


logger = logging.getLogger(__name__)

__all__ = [
    # Core configuration classes
    "Config",
    "AppConfig",
    "DatabaseConfig",
    "SecurityConfig",
    "ConfigManager",
    "ConfigValidator",
    "ValidationResult",
    "ConfigLoader",
    "ConfigTransformer",
    "ConfigLoaderProtocol",
    "ConfigValidatorProtocol",
    "ConfigTransformerProtocol",
    # Factory and management functions
    "create_config_manager",
    "get_config",
    "reload_config",
    # Convenience getters
    "get_app_config",
    "get_database_config",
    "get_security_config",
    "get_plugin_config",
    # Optional service getters
    "get_database_manager",
    "get_database_connection",
    "get_mock_connection",
    "get_enhanced_postgresql_manager",
    # Dynamic configuration
    "dynamic_config",
    "DynamicConfigManager",
    # Constants
    "SecurityConstants",
    "PerformanceConstants",
    "CSSConstants",
]
