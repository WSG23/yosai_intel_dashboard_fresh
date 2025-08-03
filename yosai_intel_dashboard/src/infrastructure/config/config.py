#!/usr/bin/env python3
"""
Simplified Configuration System
Replaces: config/yaml_config.py, config/unified_config.py, config/validator.py
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from .base import CacheConfig, Config
from .config_manager import ConfigManager, create_config_manager
from .pydantic_models import DatabaseConnectionFactoryConfig
from .schema import (
    AnalyticsSettings,
    AppSettings,
    ConfigSchema,
    DatabaseSettings,
    MonitoringSettings,
    SampleFilesSettings,
    SecretValidationSettings,
    SecuritySettings,
)

# Global configuration instance
_config_manager: Optional[ConfigManager] = None


def get_config() -> "ConfigManager":
    """Get global configuration manager using new implementation."""
    global _config_manager
    if _config_manager is None:
        from .config_manager import get_config as _new_get_config

        _config_manager = _new_get_config()

    return _config_manager


def reload_config() -> "ConfigManager":
    """Reload configuration using new implementation."""
    global _config_manager
    from .config_manager import reload_config as _new_reload

    _config_manager = _new_reload()
    return _config_manager


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


def get_sample_files_config() -> SampleFilesSettings:
    """Get sample file configuration"""
    return get_config().get_sample_files_config()


def get_analytics_config() -> AnalyticsSettings:
    """Get analytics configuration"""
    return get_config().get_analytics_config()


def get_monitoring_config() -> MonitoringSettings:
    """Get monitoring configuration"""
    return get_config().get_monitoring_config()


def get_cache_config() -> CacheConfig:
    """Get cache configuration"""
    return get_config().get_cache_config()


def get_secret_validation_config() -> SecretValidationSettings:
    """Get secret validation configuration"""
    return get_config().get_secret_validation_config()


def get_database_connection_factory_config() -> DatabaseConnectionFactoryConfig:
    """Get database connection factory configuration"""
    return get_config().get_database_connection_factory_config()


def get_plugin_config(name: str) -> Dict[str, Any]:
    """Get configuration for a specific plugin"""
    return get_config().get_plugin_config(name)


# Export main classes and functions

__all__ = [
    "Config",
    "ConfigSchema",
    "AppSettings",
    "DatabaseSettings",
    "DatabaseConnectionFactoryConfig",
    "SecuritySettings",
    "SampleFilesSettings",
    "AnalyticsSettings",
    "MonitoringSettings",
    "CacheConfig",
    "SecretValidationSettings",
    "ConfigManager",
    "create_config_manager",
    "get_config",
    "reload_config",
    "get_app_config",
    "get_database_config",
    "get_security_config",
    "get_sample_files_config",
    "get_analytics_config",
    "get_monitoring_config",
    "get_cache_config",
    "get_secret_validation_config",
    "get_database_connection_factory_config",
    "get_plugin_config",
]
