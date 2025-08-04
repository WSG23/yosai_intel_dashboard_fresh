"""High level configuration manager."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, Dict, Optional

from pydantic import ValidationError

from yosai_intel_dashboard.src.core.exceptions import ConfigurationError
from yosai_intel_dashboard.src.core.protocols import ConfigurationProtocol
from yosai_intel_dashboard.src.infrastructure.config.configuration_mixin import ConfigurationMixin

from .base import CacheConfig, Config
from .config_transformer import ConfigTransformer
from .config_validator import ConfigValidator, ValidationResult
from .environment import get_environment
from .generated.protobuf.config.schema import config_pb2
from .proto_adapter import to_dataclasses
from .protocols import (
    ConfigLoaderProtocol,
    ConfigTransformerProtocol,
    ConfigValidatorProtocol,
)
from .pydantic_models import ConfigModel, DatabaseConnectionFactoryConfig
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


class ConfigManager(ConfigurationMixin, ConfigurationProtocol):
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
        self.db_connection_factory_config: DatabaseConnectionFactoryConfig = (
            DatabaseConnectionFactoryConfig()
        )
        self.reload_config()

    def reload_config(self) -> None:
        """Reload configuration from source."""
        data = self.loader.load(self.config_path)
        raw_data: Dict[str, Any] = {}
        if isinstance(data, config_pb2.YosaiConfig):
            cfg = to_dataclasses(data)
        elif isinstance(data, dict):
            raw_data = data
            cfg = self.validator.validate(data)
        elif is_dataclass(data):
            cfg = data
            raw_data = asdict(data)
        else:
            cfg = Config()
        cfg.environment = get_environment()
        self.transformer.transform(cfg)

        factory_data = raw_data.get("database_connection_factory", {})
        self.db_connection_factory_config = (
            DatabaseConnectionFactoryConfig.model_validate(factory_data)
        )

        validation_data = asdict(cfg)
        validation_data["database_connection_factory"] = (
            self.db_connection_factory_config.model_dump()
        )

        try:
            ConfigModel.model_validate(validation_data)
        except ValidationError as exc:
            raise ConfigurationError(f"Invalid configuration: {exc}") from exc

        self.validation = self.validator.run_checks(cfg)
        self.config = ConfigSchema.from_dataclass(cfg)
        # expose common sections directly for mixin helpers
        self.security = self.config.security
        self.uploads = self.config.uploads
        # some configurations may provide performance settings
        self.performance = getattr(self.config, "performance", None)

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

    def get_database_connection_factory_config(self) -> DatabaseConnectionFactoryConfig:
        """Get database connection factory configuration."""
        return self.db_connection_factory_config

    def get_plugin_config(self, name: str) -> Dict[str, Any]:
        """Get configuration for a specific plugin."""
        return self.config.plugin_settings.get(name, {})

    # Convenience properties for legacy service components -----------------
    @property
    def metrics_interval(self) -> float:
        monitoring = self.get_monitoring_config()
        return float(
            getattr(
                monitoring,
                "metrics_interval_seconds",
                getattr(monitoring, "metrics_interval", 1.0),
            )
        )

    @property
    def ping_interval(self) -> float:
        monitoring = self.get_monitoring_config()
        return float(getattr(monitoring, "health_check_interval", 30.0))

    @property
    def ping_timeout(self) -> float:
        monitoring = self.get_monitoring_config()
        return float(getattr(monitoring, "health_check_timeout", 10.0))

    @property
    def ai_confidence_threshold(self) -> float:
        return float(self.get_ai_confidence_threshold())

    @property
    def max_upload_size_mb(self) -> int:
        return int(self.get_max_upload_size_mb())

    @property
    def upload_chunk_size(self) -> int:
        return int(self.get_upload_chunk_size())

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
