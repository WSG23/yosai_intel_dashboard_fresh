"""High level configuration manager."""
from __future__ import annotations

from typing import Any, Dict, Optional

from core.protocols import ConfigurationProtocol

from .config import AppConfig, Config, DatabaseConfig, SecurityConfig
from .config_loader import ConfigLoader, ConfigLoaderProtocol
from .config_validator import ConfigValidator, ValidationResult
from .config_transformer import ConfigTransformer
from .environment import get_environment


class ConfigManager(ConfigurationProtocol):
    """Orchestrate loading, validating and transforming configuration."""

    def __init__(
        self,
        config_path: Optional[str] = None,
        loader: ConfigLoaderProtocol | None = None,
        validator: ConfigValidator | None = None,
        transformer: ConfigTransformer | None = None,
    ) -> None:
        self.config_path = config_path
        self.loader = loader or ConfigLoader()
        self.validator = validator or ConfigValidator()
        self.transformer = transformer or ConfigTransformer()
        self.config = Config()
        self.validation: ValidationResult | None = None
        self.reload_config()

    # ------------------------------------------------------------------
    def reload_config(self) -> None:
        data = self.loader.load(self.config_path)
        if data:
            cfg = self.validator.validate(data)
        else:
            cfg = Config()
        cfg.environment = get_environment()
        self.transformer.transform(cfg)
        self.validation = self.validator.run_checks(cfg)
        self.config = cfg

    # ------------------------------------------------------------------
    def get_database_config(self) -> DatabaseConfig:
        return self.config.database

    def get_app_config(self) -> AppConfig:
        return self.config.app

    def get_security_config(self) -> SecurityConfig:
        return self.config.security

    def get_upload_config(self) -> Dict[str, Any]:
        return {}

    def validate_config(self) -> Dict[str, Any]:
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
    global _manager
    if _manager is None:
        _manager = ConfigManager()
    return _manager


def reload_config() -> ConfigManager:
    global _manager
    _manager = ConfigManager()
    return _manager


__all__ = ["ConfigManager", "get_config", "reload_config"]
