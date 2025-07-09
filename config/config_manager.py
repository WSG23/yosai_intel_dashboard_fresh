"""High level configuration manager."""

from __future__ import annotations

from typing import Any, Dict, Optional

from core.protocols import ConfigurationProtocol

from .base import (
    AppConfig,
    CacheConfig,
    Config,
    DatabaseConfig,
    MonitoringConfig,
    SampleFilesConfig,
    SecretValidationConfig,
    AnalyticsConfig,
    SecurityConfig,
)
from .config_loader import ConfigLoader
from .config_transformer import ConfigTransformer
from .config_validator import ConfigValidator, ValidationResult
from .environment import get_environment
from .protocols import (
    ConfigLoaderProtocol,
    ConfigTransformerProtocol,
    ConfigValidatorProtocol,
)


class ConfigManager(ConfigurationProtocol):
    """Orchestrate loading, validating and transforming configuration."""

    def __init__(
        self,
        config_path: Optional[str] = None,
        loader: ConfigLoaderProtocol | None = None,
        validator: ConfigValidatorProtocol | None = None,
        transformer: ConfigTransformerProtocol | None = None,
    ) -> None:
        self.config_path = config_path
        self.loader: ConfigLoaderProtocol = loader or ConfigLoader()
        self.validator: ConfigValidatorProtocol = validator or ConfigValidator()
        self.transformer: ConfigTransformerProtocol = transformer or ConfigTransformer()
        self.config = Config()
        self.validation: ValidationResult | None = None
        self.reload_config()

    def reload_config(self) -> None:
        """Reload configuration from source."""
        data = self.loader.load(self.config_path)
        if data:
            cfg = self.validator.validate(data)
        else:
            cfg = Config()
        cfg.environment = get_environment()
        self.transformer.transform(cfg)
        self.validation = self.validator.run_checks(cfg)
        self.config = cfg

    def get_database_config(self) -> DatabaseConfig:
        """Get database configuration."""
        return self.config.database

    def get_app_config(self) -> AppConfig:
        """Get app configuration."""
        return self.config.app

    def get_security_config(self) -> SecurityConfig:
        """Get security configuration."""
        return self.config.security

    def get_sample_files_config(self) -> SampleFilesConfig:
        """Get sample files configuration."""
        return self.config.sample_files

    def get_analytics_config(self) -> AnalyticsConfig:
        """Get analytics configuration."""
        return self.config.analytics

    def get_monitoring_config(self) -> MonitoringConfig:
        """Get monitoring configuration."""
        return self.config.monitoring

    def get_cache_config(self) -> CacheConfig:
        """Get cache configuration."""
        return self.config.cache

    def get_secret_validation_config(self) -> SecretValidationConfig:
        """Get secret validation configuration."""
        return self.config.secret_validation

    def get_plugin_config(self, name: str) -> Dict[str, Any]:
        """Get configuration for a specific plugin."""
        return self.config.plugin_settings.get(name, {})

    def get_upload_config(self) -> Dict[str, Any]:
        """Get upload configuration settings."""
        return {}

    def validate_config(self) -> Dict[str, Any]:
        """Validate current configuration and return results."""
        if not self.validation:
            self.validation = self.validator.run_checks(self.config)
        return {
            "valid": self.validation.valid,
            "errors": list(self.validation.errors),
            "warnings": list(self.validation.warnings),
        }


# Global cache
_manager: Optional[ConfigManager] = None


def get_config() -> ConfigManager:
    """Get global configuration manager instance."""
    global _manager
    if _manager is None:
        _manager = ConfigManager()
    return _manager


def reload_config() -> ConfigManager:
    """Reload global configuration manager."""
    global _manager
    _manager = ConfigManager()
    return _manager


def create_config_manager(config_path: Optional[str] = None) -> ConfigManager:
    """Factory for creating :class:`ConfigManager` instances."""
    return ConfigManager(config_path=config_path)


__all__ = [
    "ConfigManager",
    "get_config",
    "reload_config",
    "create_config_manager",
]
