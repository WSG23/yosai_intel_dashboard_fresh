#!/usr/bin/env python3
"""
Simplified Configuration System
Replaces: config/yaml_config.py, config/unified_config.py, config/validator.py
"""
from typing import Any, Dict

from .base import (
    AppConfig,
    AnalyticsConfig,
    CacheConfig,
    Config,
    DatabaseConfig,
    MonitoringConfig,
    SampleFilesConfig,
    SecretValidationConfig,
    SecurityConfig,
)
from .config_manager import (
    ConfigManager,
    create_config_manager,
    get_config,
    reload_config,
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


def get_sample_files_config() -> SampleFilesConfig:
    """Get sample file configuration"""
    return get_config().get_sample_files_config()


def get_analytics_config() -> AnalyticsConfig:
    """Get analytics configuration"""
    return get_config().get_analytics_config()


def get_monitoring_config() -> MonitoringConfig:
    """Get monitoring configuration"""
    return get_config().get_monitoring_config()


def get_cache_config() -> CacheConfig:
    """Get cache configuration"""
    return get_config().get_cache_config()


def get_secret_validation_config() -> SecretValidationConfig:
    """Get secret validation configuration"""
    return get_config().get_secret_validation_config()


def get_plugin_config(name: str) -> Dict[str, Any]:
    """Get configuration for a specific plugin"""
    return get_config().get_plugin_config(name)




# Export main classes and functions
__all__ = [
    "Config",
    "AppConfig",
    "DatabaseConfig",
    "SecurityConfig",
    "SampleFilesConfig",
    "AnalyticsConfig",
    "MonitoringConfig",
    "CacheConfig",
    "SecretValidationConfig",
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
    "get_plugin_config",
]

