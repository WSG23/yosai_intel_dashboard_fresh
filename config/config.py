#!/usr/bin/env python3
"""
Simplified Configuration System
Replaces: config/yaml_config.py, config/unified_config.py, config/validator.py
"""
import os
from pathlib import Path
import yaml
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List

from .dynamic_config import dynamic_config
from .environment import get_environment, select_config_file
from .config_validator import ConfigValidator
from core.secrets_validator import SecretsValidator
from core.exceptions import ConfigurationError

logger = logging.getLogger(__name__)


@dataclass
class AppConfig:
    """Application configuration"""

    title: str = "Yōsai Intel Dashboard"
    debug: bool = True
    host: str = "127.0.0.1"
    port: int = 8050
    secret_key: str = field(default_factory=lambda: os.getenv("SECRET_KEY", ""))
    environment: str = "development"


@dataclass
class DatabaseConfig:
    """Database configuration"""

    type: str = "sqlite"
    host: str = "localhost"
    port: int = 5432
    name: str = "yosai.db"
    user: str = "user"
    password: str = ""
    connection_pool_size: int = dynamic_config.get_db_pool_size()
    connection_timeout: int = 30
    initial_pool_size: int = dynamic_config.get_db_pool_size()
    max_pool_size: int = dynamic_config.get_db_pool_size()
    shrink_timeout: int = 60

    def get_connection_string(self) -> str:
        """Get database connection string"""
        if self.type == "postgresql":
            return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"
        elif self.type == "sqlite":
            return f"sqlite:///{self.name}"
        else:
            return f"mock://{self.name}"


@dataclass
class SecurityConfig:
    """Security configuration"""

    secret_key: str = field(default_factory=lambda: os.getenv("SECRET_KEY", ""))
    session_timeout: int = 3600
    cors_origins: List[str] = field(default_factory=list)
    csrf_enabled: bool = True
    max_failed_attempts: int = 5


@dataclass
class SampleFilesConfig:
    """File paths for bundled sample datasets"""

    csv_path: str = "data/sample_data.csv"
    json_path: str = "data/sample_data.json"


@dataclass
class Config:
    """Main configuration object"""

    app: AppConfig = field(default_factory=AppConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    sample_files: SampleFilesConfig = field(default_factory=SampleFilesConfig)
    environment: str = "development"
    plugins: Dict[str, Any] = field(default_factory=dict)


class ConfigManager:
    """Simple configuration manager"""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path
        self.config = Config()
        self.validated_secrets: Dict[str, str] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from YAML file and environment"""
        self.config.environment = get_environment()
        # Load from YAML file
        yaml_config = self._load_yaml_config()

        # Apply YAML config
        if yaml_config:
            self.config = ConfigValidator.validate(yaml_config)
            if "plugins" in yaml_config:
                self.config.plugins = yaml_config.get("plugins", {})

        # Apply environment overrides
        self._apply_env_overrides()

        # Validate secrets and store values
        validator = SecretsValidator()
        self.validated_secrets = validator.validate_all_secrets()
        self._apply_validated_secrets()

        # Validate configuration
        self._validate_config()

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
                data = yaml.safe_load(content) or {}

            # Load plugin configuration
            plugin_path = Path(__file__).resolve().parents[1] / "core" / "plugins" / "config" / "plugins.yaml"
            if plugin_path.exists():
                with open(plugin_path, "r") as pf:
                    plugin_data = yaml.safe_load(pf) or {}
                if "plugins" in plugin_data:
                    if "plugins" in data and isinstance(data["plugins"], dict):
                        data["plugins"].update(plugin_data["plugins"])
                    else:
                        data["plugins"] = plugin_data["plugins"]

            return data
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
            self.config.database.connection_pool_size = db_data.get(
                "connection_pool_size", self.config.database.connection_pool_size
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

    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides"""
        # App overrides
        if os.getenv("DEBUG"):
            self.config.app.debug = os.getenv("DEBUG", "").lower() in (
                "true",
                "1",
                "yes",
            )
        host_env = os.getenv("HOST")
        if host_env is not None:
            self.config.app.host = host_env
        port_env = os.getenv("PORT")
        if port_env is not None:
            self.config.app.port = int(port_env)
        secret_env = os.getenv("SECRET_KEY")
        if secret_env is not None:
            self.config.app.secret_key = secret_env
            self.config.security.secret_key = secret_env
        title_env = os.getenv("APP_TITLE")
        if title_env is not None:
            self.config.app.title = title_env

        # Database overrides
        db_type = os.getenv("DB_TYPE")
        if db_type is not None:
            self.config.database.type = db_type
        db_host = os.getenv("DB_HOST")
        if db_host is not None:
            self.config.database.host = db_host
        db_port = os.getenv("DB_PORT")
        if db_port is not None:
            self.config.database.port = int(db_port)
        db_name = os.getenv("DB_NAME")
        if db_name is not None:
            self.config.database.name = db_name
        db_user = os.getenv("DB_USER")
        if db_user is not None:
            self.config.database.user = db_user
        db_password = os.getenv("DB_PASSWORD")
        if db_password is not None:
            self.config.database.password = db_password
        # Pool size is loaded from DynamicConfigManager
        self.config.database.connection_pool_size = dynamic_config.get_db_pool_size()
        db_timeout = os.getenv("DB_TIMEOUT")
        if db_timeout is not None:
            self.config.database.connection_timeout = int(db_timeout)
        init_pool = os.getenv("DB_INITIAL_POOL_SIZE")
        if init_pool is not None:
            self.config.database.initial_pool_size = int(init_pool)
        max_pool = os.getenv("DB_MAX_POOL_SIZE")
        if max_pool is not None:
            self.config.database.max_pool_size = int(max_pool)
        shrink_timeout = os.getenv("DB_SHRINK_TIMEOUT")
        if shrink_timeout is not None:
            self.config.database.shrink_timeout = int(shrink_timeout)

        # Security overrides
        csrf_enabled = os.getenv("CSRF_ENABLED")
        if csrf_enabled is not None:
            self.config.security.csrf_enabled = csrf_enabled.lower() in (
                "true",
                "1",
                "yes",
            )
        max_failed = os.getenv("MAX_FAILED_ATTEMPTS")
        if max_failed is not None:
            self.config.security.max_failed_attempts = int(max_failed)

        # Sample file overrides
        sample_csv = os.getenv("SAMPLE_CSV_PATH")
        if sample_csv is not None:
            self.config.sample_files.csv_path = sample_csv
        sample_json = os.getenv("SAMPLE_JSON_PATH")
        if sample_json is not None:
            self.config.sample_files.json_path = sample_json

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

            if self.config.app.host == "127.0.0.1":
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

    def get_app_config(self) -> AppConfig:
        """Get app configuration"""
        return self.config.app

    def get_database_config(self) -> DatabaseConfig:
        """Get database configuration"""
        return self.config.database

    def get_security_config(self) -> SecurityConfig:
        """Get security configuration"""
        return self.config.security

    def get_sample_files_config(self) -> SampleFilesConfig:
        """Get sample file path configuration"""
        return self.config.sample_files

    def get_plugins_config(self) -> Dict[str, Any]:
        """Return full plugins configuration dictionary"""
        return self.config.plugins

    def get_plugin_config(self, name: str) -> Dict[str, Any]:
        """Return configuration for a specific plugin"""
        return self.config.plugins.get(name, {})


# Global configuration instance
_config_manager: Optional[ConfigManager] = None


def get_config() -> ConfigManager:
    """Get global configuration manager"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def reload_config() -> ConfigManager:
    """Reload configuration (useful for testing)"""
    global _config_manager
    _config_manager = None
    return get_config()


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


def get_plugins_config() -> Dict[str, Any]:
    """Get full plugins configuration"""
    return get_config().get_plugins_config()


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
    "ConfigManager",
    "get_config",
    "reload_config",
    "get_app_config",
    "get_database_config",
    "get_security_config",
    "get_sample_files_config",
    "get_plugins_config",
    "get_plugin_config",
]
