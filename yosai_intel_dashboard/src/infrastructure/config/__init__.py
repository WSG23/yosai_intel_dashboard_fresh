"""Configuration module with proper imports and error handling."""

import logging
from typing import Any, Dict, Optional

from .app_config import UploadConfig
from .base import Config
from .config_manager import ConfigManager, get_config, reload_config
from .config_transformer import ConfigTransformer
from .config_validator import ConfigValidator, ValidationResult
from .constants import CSSConstants, PerformanceConstants, SecurityConstants
from .dynamic_config import DynamicConfigManager, dynamic_config
from .environment_processor import EnvironmentProcessor
from .hierarchical_loader import HierarchicalLoader
from .proto_adapter import to_dataclasses
from .protocols import (
    ConfigLoaderProtocol,
    ConfigTransformerProtocol,
    ConfigValidatorProtocol,
)
from .schema import (
    AppSettings,
    ConfigSchema,
    DatabaseSettings,
    SecuritySettings,
)
from .secure_config_manager import SecureConfigManager
from .secure_db import execute_secure_query
from .unicode_handler import UnicodeHandler
from .unified_loader import UnifiedLoader


def create_config_manager(
    config_path: Optional[str] = None,
    *,
    container: Optional[Any] = None,
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

    loader = loader or UnifiedLoader()
    validator = validator or ConfigValidator()
    transformer = transformer or ConfigTransformer()

    return ConfigManager(
        config_path=config_path,
        loader=loader,
        validator=validator,
        transformer=transformer,
    )


# Convenience functions
def get_app_config() -> AppSettings:
    """Get app configuration"""
    return get_config().get_app_config()


def get_database_config() -> DatabaseSettings:
    """Get database configuration"""
    return get_config().get_database_config()


def get_security_config() -> SecuritySettings:
    """Get security configuration"""
    return get_config().get_security_config()


def get_plugin_config(name: str) -> Dict[str, Any]:
    """Get configuration for a specific plugin"""
    return get_config().get_plugin_config(name)


logger = logging.getLogger(__name__)

__all__ = [
    # Core configuration classes
    "Config",
    "ConfigSchema",
    "AppSettings",
    "DatabaseSettings",
    "SecuritySettings",
    "UploadConfig",
    "ConfigManager",
    "SecureConfigManager",
    "EnvironmentProcessor",
    "ConfigValidator",
    "ValidationResult",
    "HierarchicalLoader",
    "ConfigTransformer",
    "UnifiedLoader",
    "to_dataclasses",
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
    # Dynamic configuration
    "dynamic_config",
    "DynamicConfigManager",
    # Constants
    "SecurityConstants",
    "PerformanceConstants",
    "CSSConstants",
    "execute_secure_query",
    "UnicodeHandler",
]


def get_monitoring_config() -> Dict[str, Any]:
    """Get monitoring configuration."""
    try:
        return get_app_config().monitoring
    except AttributeError:
        # Return default monitoring config
        return {
            "enabled": True,
            "data_quality_checks": True,
            "alert_thresholds": {"error_rate": 0.05, "processing_time": 30},
        }
