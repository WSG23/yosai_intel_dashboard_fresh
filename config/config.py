#!/usr/bin/env python3
"""
Simplified Configuration System
Replaces: config/yaml_config.py, config/unified_config.py, config/validator.py
"""
import logging
import os
from typing import Any, Dict, List, Optional

import yaml

from core.exceptions import ConfigurationError
from core.protocols import ConfigurationProtocol
from core.secrets_manager import SecretsManager
from core.secrets_validator import SecretsValidator


from .config_loader import ConfigLoader
from .config_validator import ConfigValidator, ValidationResult
from .base import (
    AppConfig,
    AnalyticsConfig,
    CacheConfig,
    Config,
    ConfigTransformer,
    DatabaseConfig,
    MonitoringConfig,
    SampleFilesConfig,
    SecretValidationConfig,
    SecurityConfig,
)
from .constants import (
    DEFAULT_APP_HOST,
    DEFAULT_APP_PORT,
    DEFAULT_CACHE_HOST,
    DEFAULT_CACHE_PORT,
    DEFAULT_DB_HOST,
    DEFAULT_DB_PORT,
)
from .dynamic_config import dynamic_config
from .environment import get_environment, select_config_file

logger = logging.getLogger(__name__)


def _validate_production_secrets() -> None:
    """Ensure required secrets are set when running in production."""
    if os.getenv("YOSAI_ENV") == "production":
        secret = os.getenv("SECRET_KEY")
        if not secret:
            raise ConfigurationError("SECRET_KEY required in production")




class ConfigManager(ConfigurationProtocol):
    """Simple configuration manager"""

    def __init__(
        self,
        config_path: Optional[str] = None,
        *,
        loader: Optional[ConfigLoader] = None,
        validator: Optional[ConfigValidator] = None,
        transformer: Optional[ConfigTransformer] = None,
    ) -> None:
        self.config_path = config_path
        self.loader = loader or ConfigLoader(config_path)
        self.validator = validator or ConfigValidator()
        self.transformer = transformer or ConfigTransformer()
        self.config = Config()
        self.validated_secrets: Dict[str, str] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from YAML file and environment"""
        self.config.environment = get_environment()
        _validate_production_secrets()
        # Load from YAML file
        yaml_config = self.loader.load()

        # Apply YAML config
        if yaml_config:
            self.config = self.validator.validate(yaml_config)
            self._apply_yaml_config(yaml_config)

        # Apply environment overrides
        self._apply_env_overrides()

        # Validate secrets and store values
        validator = SecretsValidator()
        self.validated_secrets = validator.validate_all_secrets()
        self._apply_validated_secrets()

        # Validate configuration
        self._validate_config()
        self.config = self.transformer.transform(self.config)

    def _load_yaml_config(self) -> Optional[Dict[str, Any]]:
        """Load configuration from YAML file"""
        config_file = select_config_file(self.config_path)

        if not config_file or not config_file.exists():
            logger.info("No YAML config file found, using defaults")
            return None

        try:
            with open(config_file, "r") as f:
                content = f.read()
                # Simple environment variable substitution
                content = self._substitute_env_vars(content)

                class IncludeLoader(yaml.SafeLoader):
                    pass

                base_dir = config_file.parent

                def _include(loader: IncludeLoader, node: yaml.Node):
                    filename = loader.construct_scalar(node)
                    inc_path = base_dir / filename
                    with open(inc_path, "r") as inc:
                        return yaml.load(inc, Loader=IncludeLoader)

                IncludeLoader.add_constructor("!include", _include)

                return yaml.load(content, Loader=IncludeLoader)
        except Exception as e:
            logger.warning(f"Error loading config file {config_file}: {e}")
            return None

    def _substitute_env_vars(self, content: str) -> str:
        """Replace ${VAR_NAME} with environment variable values"""
        import re

        def replacer(match):
            var_name = match.group(1)
            return os.getenv(var_name, match.group(0))

        return re.sub(r"\$\{([^}]+)\}", replacer, content)

    def _apply_yaml_config(self, yaml_config: Dict[str, Any]) -> None:
        """Apply YAML configuration to config objects"""
        if "app" in yaml_config:
            app_data = yaml_config["app"]
            self.config.app.title = app_data.get("title", self.config.app.title)
            self.config.app.debug = app_data.get("debug", self.config.app.debug)
            self.config.app.host = app_data.get("host", self.config.app.host)
            self.config.app.port = app_data.get("port", self.config.app.port)
            self.config.app.secret_key = app_data.get(
                "secret_key", self.config.app.secret_key
            )

        if "database" in yaml_config:
            db_data = yaml_config["database"]
            self.config.database.type = db_data.get("type", self.config.database.type)
            self.config.database.host = db_data.get("host", self.config.database.host)
            self.config.database.port = db_data.get("port", self.config.database.port)
            self.config.database.name = db_data.get("name", self.config.database.name)
            self.config.database.user = db_data.get("user", self.config.database.user)
            self.config.database.password = db_data.get(
                "password", self.config.database.password
            )
            self.config.database.connection_timeout = db_data.get(
                "connection_timeout", self.config.database.connection_timeout
            )
            self.config.database.initial_pool_size = db_data.get(
                "initial_pool_size", self.config.database.initial_pool_size
            )
            self.config.database.max_pool_size = db_data.get(
                "max_pool_size", self.config.database.max_pool_size
            )
            self.config.database.shrink_timeout = db_data.get(
                "shrink_timeout", self.config.database.shrink_timeout
            )

        if "security" in yaml_config:
            sec_data = yaml_config["security"]
            self.config.security.secret_key = sec_data.get(
                "secret_key", self.config.security.secret_key
            )
            self.config.security.session_timeout = sec_data.get(
                "session_timeout", self.config.security.session_timeout
            )
            if "session_timeout_by_role" in sec_data:
                self.config.security.session_timeout_by_role = sec_data.get(
                    "session_timeout_by_role",
                    self.config.security.session_timeout_by_role,
                )
            self.config.security.cors_origins = sec_data.get(
                "cors_origins", self.config.security.cors_origins
            )
            if "csrf_enabled" in sec_data:
                self.config.security.csrf_enabled = bool(sec_data.get("csrf_enabled"))
            if "max_failed_attempts" in sec_data:
                self.config.security.max_failed_attempts = int(
                    sec_data.get("max_failed_attempts")
                )

        if "sample_files" in yaml_config:
            sample_data = yaml_config["sample_files"]
            self.config.sample_files.csv_path = sample_data.get(
                "csv_path", self.config.sample_files.csv_path
            )
            self.config.sample_files.json_path = sample_data.get(
                "json_path", self.config.sample_files.json_path
            )

        if "analytics" in yaml_config:
            analytics_data = yaml_config["analytics"]
            for key, value in analytics_data.items():
                if hasattr(self.config.analytics, key):
                    if key == "max_display_rows":
                        setattr(self.config.analytics, key, int(value))
                    else:
                        setattr(self.config.analytics, key, value)

        if "monitoring" in yaml_config:
            mon_data = yaml_config["monitoring"]
            for key, value in mon_data.items():
                if hasattr(self.config.monitoring, key):
                    setattr(self.config.monitoring, key, value)

        if "cache" in yaml_config:
            cache_data = yaml_config["cache"]
            for key, value in cache_data.items():
                if hasattr(self.config.cache, key):
                    setattr(self.config.cache, key, value)

        if "secret_validation" in yaml_config:
            sec_val = yaml_config["secret_validation"]
            for key, value in sec_val.items():
                if hasattr(self.config.secret_validation, key):
                    setattr(self.config.secret_validation, key, value)

        if "plugins" in yaml_config:
            plugins_data = yaml_config["plugins"]
            if isinstance(plugins_data, dict):
                self.config.plugin_settings.update(plugins_data)

    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides"""
        config_transformer.apply(self)


    def _apply_validated_secrets(self) -> None:
        """Apply secrets validated by SecretsValidator."""
        if "SECRET_KEY" in self.validated_secrets:
            secret = self.validated_secrets["SECRET_KEY"]
            self.config.app.secret_key = secret
            self.config.security.secret_key = secret
            os.environ.setdefault("SECRET_KEY", secret)
        if "DB_PASSWORD" in self.validated_secrets:
            pwd = self.validated_secrets["DB_PASSWORD"]
            self.config.database.password = pwd
            os.environ.setdefault("DB_PASSWORD", pwd)

    def _validate_config(self) -> None:
        """Validate configuration and log warnings"""
        warnings = []
        errors = []

        validator = SecretsValidator()

        invalid_secrets: List[str] = []

        # Production checks
        if self.config.environment == "production":
            invalid_secrets = validator.validate_production_secrets()

            if self.config.app.secret_key in [
                "dev-key-change-in-production",
                "change-me",
                "",
            ]:
                errors.append("SECRET_KEY must be set for production")

            if (
                not self.config.database.password
                and self.config.database.type != "sqlite"
            ):
                warnings.append("Production database requires password")

            if self.config.app.host == DEFAULT_APP_HOST:
                warnings.append("Production should not run on localhost")

        if self.config.app.debug and self.config.app.host == "0.0.0.0":
            warnings.append("Debug mode with host 0.0.0.0 is a security risk")
        if (
            self.config.database.type == "postgresql"
            and not self.config.database.password
        ):
            warnings.append("PostgreSQL requires a password")

        # Log warnings
        for warning in warnings:
            logger.warning(f"Configuration warning: {warning}")

        if invalid_secrets:
            secret_list = ", ".join(invalid_secrets)
            logger.error(f"Invalid production secrets: {secret_list}")
            raise ValueError(f"Invalid secrets: {secret_list}")

        if errors:
            error_msg = "; ".join(errors)
            logger.error(error_msg)
            raise ConfigurationError(error_msg)

    def validate_current_config(self) -> List[ValidationResult]:
        """Run validation rules and return results."""
        results: List[ValidationResult] = []
        results.extend(ConfigValidator.validate_structure(self.config))
        results.extend(ConfigValidator.validate_values(self.config))
        results.extend(ConfigValidator.validate_environment_specific(self.config))
        return results

    def get_app_config(self) -> AppConfig:
        """Get app configuration"""
        return self.config.app

    def get_database_config(self) -> DatabaseConfig:
        """Get database configuration"""
        return self.config.database

    def get_security_config(self) -> SecurityConfig:
        """Get security configuration"""
        return self.config.security

    def get_upload_config(self) -> Dict[str, Any]:
        """Get upload configuration settings"""
        return vars(dynamic_config.uploads)

    def get_sample_files_config(self) -> SampleFilesConfig:
        """Get sample file path configuration"""
        return self.config.sample_files

    def get_analytics_config(self) -> AnalyticsConfig:
        """Get analytics configuration"""
        return self.config.analytics

    def get_monitoring_config(self) -> MonitoringConfig:
        """Get monitoring configuration"""
        return self.config.monitoring

    def get_cache_config(self) -> CacheConfig:
        """Get cache configuration"""
        return self.config.cache

    def get_secret_validation_config(self) -> SecretValidationConfig:
        """Get secret validation configuration"""
        return self.config.secret_validation

    def get_plugin_config(self, name: str) -> Dict[str, Any]:
        """Return configuration dictionary for the given plugin."""
        return self.config.plugin_settings.get(name, {})

    # ------------------------------------------------------------------
    def reload_config(self) -> None:
        """Reload configuration from source."""
        self._load_config()

    def validate_config(self) -> Dict[str, Any]:
        """Validate current configuration."""
        try:
            self._validate_config()
            return {"valid": True}
        except Exception as exc:
            return {"valid": False, "error": str(exc)}


def create_config_manager(config_path: Optional[str] = None) -> "ConfigManager":
    """Factory helper to instantiate :class:`ConfigManager`."""
    return ConfigManager(config_path)



# Global configuration instance
_config_manager: Optional[ConfigManager] = None


def get_config() -> ConfigManager:
    """Get global configuration manager using new implementation."""
    global _config_manager
    if _config_manager is None:
        from .config_manager import get_config as _new_get_config

        _config_manager = _new_get_config()

    return _config_manager


def reload_config() -> ConfigManager:
    """Reload configuration using new implementation."""
    global _config_manager
    from .config_manager import reload_config as _new_reload

    _config_manager = _new_reload()
    return _config_manager


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


def create_config_manager(config_path: Optional[str] = None) -> ConfigManager:
    """Factory for creating :class:`ConfigManager` instances."""
    return ConfigManager(config_path=config_path)


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
    "create_config_manager",
]

# Use new implementation by default
from .config_manager import ConfigManager as ConfigManager
from .config_manager import get_config as get_config
from .config_manager import reload_config as reload_config
