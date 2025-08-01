"""High level configuration manager."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, Dict, Optional

from pydantic import ValidationError

from yosai_intel_dashboard.src.core.exceptions import ConfigurationError
from yosai_intel_dashboard.src.core.protocols import ConfigurationProtocol

from .base import CacheConfig, Config
from .config_transformer import ConfigTransformer
from .config_validator import ConfigValidator, ValidationResult
from .environment import get_environment
from .generated.protobuf.config.schema import config_pb2
from .hierarchical_loader import HierarchicalLoader
from .proto_adapter import to_dataclasses
from .protocols import (
    ConfigLoaderProtocol,
    ConfigTransformerProtocol,
    ConfigValidatorProtocol,
)
from .pydantic_models import ConfigModel
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
from .unified_loader import UnifiedLoader


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
        self.loader: ConfigLoaderProtocol = loader or UnifiedLoader()
        self.validator: ConfigValidatorProtocol = validator or ConfigValidator()
        self.transformer: ConfigTransformerProtocol = transformer or ConfigTransformer()
        self.config: ConfigSchema = ConfigSchema()
        self.validation: ValidationResult | None = None
        self.reload_config()

    def reload_config(self) -> None:
        """Reload configuration from source."""
        data = self.loader.load(self.config_path)
        if isinstance(data, config_pb2.YosaiConfig):
            cfg = to_dataclasses(data)
        elif isinstance(data, dict):
            cfg = self.validator.validate(data)
        elif is_dataclass(data):
            cfg = data
        else:
            cfg = Config()
        cfg.environment = get_environment()
        self.transformer.transform(cfg)
        try:
            ConfigModel.model_validate(asdict(cfg))
        except ValidationError as exc:
            raise ConfigurationError(f"Invalid configuration: {exc}") from exc

        self.validation = self.validator.run_checks(cfg)
        self.config = ConfigSchema.from_dataclass(cfg)

    def get_database_config(self) -> DatabaseSettings:
        """Get database configuration."""
        return self.config.database

    def get_app_config(self) -> AppSettings:
        """Get app configuration."""
        return self.config.app

    def get_security_config(self) -> SecuritySettings:
        """Get security configuration."""
        return self.config.security

    def get_sample_files_config(self) -> SampleFilesSettings:
        """Get sample files configuration."""
        return self.config.sample_files

    def get_analytics_config(self) -> AnalyticsSettings:
        """Get analytics configuration."""
        return self.config.analytics

    def get_monitoring_config(self) -> MonitoringSettings:
        """Get monitoring configuration."""
        return self.config.monitoring

    def get_cache_config(self) -> CacheConfig:
        """Get cache configuration."""
        return self.config.cache

    def get_secret_validation_config(self) -> SecretValidationSettings:
        """Get secret validation configuration."""
        return self.config.secret_validation

    def get_plugin_config(self, name: str) -> Dict[str, Any]:
        """Get configuration for a specific plugin."""
        return self.config.plugin_settings.get(name, {})

    def get_upload_config(self) -> Dict[str, Any]:
        """Get upload configuration settings."""
        return vars(self.config.uploads)

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
    return ConfigManager(config_path=config_path, loader=UnifiedLoader())


__all__ = [
    "ConfigManager",
    "get_config",
    "reload_config",
    "create_config_manager",
]
