#!/usr/bin/env python3
"""
Simplified Configuration System
Replaces: config/yaml_config.py, config/unified_config.py, config/validator.py
"""
import os
import yaml
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


@dataclass
class AppConfig:
    """Application configuration"""
    debug: bool = True
    host: str = "127.0.0.1"
    port: int = 8050
    secret_key: str = "dev-key-change-in-production"
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
    secret_key: str = "dev-key-change-in-production"
    session_timeout: int = 3600
    cors_origins: List[str] = field(default_factory=list)


@dataclass
class Config:
    """Main configuration object"""
    app: AppConfig = field(default_factory=AppConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    environment: str = "development"


class ConfigManager:
    """Simple configuration manager"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path
        self.config = Config()
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from YAML file and environment"""
        # Load from YAML file
        yaml_config = self._load_yaml_config()
        
        # Apply YAML config
        if yaml_config:
            self._apply_yaml_config(yaml_config)
        
        # Apply environment overrides
        self._apply_env_overrides()
        
        # Validate configuration
        self._validate_config()
    
    def _load_yaml_config(self) -> Optional[Dict[str, Any]]:
        """Load configuration from YAML file"""
        config_file = self._determine_config_file()
        
        if not config_file or not config_file.exists():
            logger.info("No YAML config file found, using defaults")
            return None
        
        try:
            with open(config_file, 'r') as f:
                content = f.read()
                # Simple environment variable substitution
                content = self._substitute_env_vars(content)
                return yaml.safe_load(content)
        except Exception as e:
            logger.warning(f"Error loading config file {config_file}: {e}")
            return None
    
    def _determine_config_file(self) -> Optional[Path]:
        """Determine which config file to use"""
        # Use explicit path if provided
        if self.config_path:
            return Path(self.config_path)
        
        # Check environment variable
        env_file = os.getenv("YOSAI_CONFIG_FILE")
        if env_file:
            return Path(env_file)
        
        # Use environment-based config
        env = os.getenv("YOSAI_ENV", "development").lower()
        self.config.environment = env
        
        config_dir = Path("config")
        
        # Try environment-specific files
        env_files = {
            "production": config_dir / "production.yaml",
            "staging": config_dir / "staging.yaml", 
            "test": config_dir / "test.yaml",
            "development": config_dir / "config.yaml"
        }
        
        config_file = env_files.get(env, config_dir / "config.yaml")
        return config_file if config_file.exists() else None
    
    def _substitute_env_vars(self, content: str) -> str:
        """Replace ${VAR_NAME} with environment variable values"""
        import re
        
        def replacer(match):
            var_name = match.group(1)
            return os.getenv(var_name, match.group(0))
        
        return re.sub(r'\$\{([^}]+)\}', replacer, content)
    
    def _apply_yaml_config(self, yaml_config: Dict[str, Any]) -> None:
        """Apply YAML configuration to config objects"""
        if "app" in yaml_config:
            app_data = yaml_config["app"]
            self.config.app.debug = app_data.get("debug", self.config.app.debug)
            self.config.app.host = app_data.get("host", self.config.app.host)
            self.config.app.port = app_data.get("port", self.config.app.port)
            self.config.app.secret_key = app_data.get("secret_key", self.config.app.secret_key)
        
        if "database" in yaml_config:
            db_data = yaml_config["database"]
            self.config.database.type = db_data.get("type", self.config.database.type)
            self.config.database.host = db_data.get("host", self.config.database.host)
            self.config.database.port = db_data.get("port", self.config.database.port)
            self.config.database.name = db_data.get("name", self.config.database.name)
            self.config.database.user = db_data.get("user", self.config.database.user)
            self.config.database.password = db_data.get("password", self.config.database.password)
        
        if "security" in yaml_config:
            sec_data = yaml_config["security"]
            self.config.security.secret_key = sec_data.get("secret_key", self.config.security.secret_key)
            self.config.security.session_timeout = sec_data.get("session_timeout", self.config.security.session_timeout)
            self.config.security.cors_origins = sec_data.get("cors_origins", self.config.security.cors_origins)
    
    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides"""
        # App overrides
        if os.getenv("DEBUG"):
            self.config.app.debug = os.getenv("DEBUG", "").lower() in ("true", "1", "yes")
        if os.getenv("HOST"):
            self.config.app.host = os.getenv("HOST")
        if os.getenv("PORT"):
            self.config.app.port = int(os.getenv("PORT"))
        if os.getenv("SECRET_KEY"):
            self.config.app.secret_key = os.getenv("SECRET_KEY")
            self.config.security.secret_key = os.getenv("SECRET_KEY")
        
        # Database overrides
        if os.getenv("DB_TYPE"):
            self.config.database.type = os.getenv("DB_TYPE")
        if os.getenv("DB_HOST"):
            self.config.database.host = os.getenv("DB_HOST")
        if os.getenv("DB_PORT"):
            self.config.database.port = int(os.getenv("DB_PORT"))
        if os.getenv("DB_NAME"):
            self.config.database.name = os.getenv("DB_NAME")
        if os.getenv("DB_USER"):
            self.config.database.user = os.getenv("DB_USER")
        if os.getenv("DB_PASSWORD"):
            self.config.database.password = os.getenv("DB_PASSWORD")
    
    def _validate_config(self) -> None:
        """Validate configuration and log warnings"""
        warnings = []
        
        # Production checks
        if self.config.environment == "production":
            if self.config.app.secret_key in ["dev-key-change-in-production", "change-me"]:
                warnings.append("Production requires secure SECRET_KEY")
            
            if not self.config.database.password and self.config.database.type != "sqlite":
                warnings.append("Production database requires password")
            
            if self.config.app.host == "127.0.0.1":
                warnings.append("Production should not run on localhost")
        
        # Log warnings
        for warning in warnings:
            logger.warning(f"Configuration warning: {warning}")
    
    def get_app_config(self) -> AppConfig:
        """Get app configuration"""
        return self.config.app
    
    def get_database_config(self) -> DatabaseConfig:
        """Get database configuration"""
        return self.config.database
    
    def get_security_config(self) -> SecurityConfig:
        """Get security configuration"""
        return self.config.security


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


# Export main classes and functions
__all__ = [
    'Config', 'AppConfig', 'DatabaseConfig', 'SecurityConfig',
    'ConfigManager', 'get_config', 'reload_config',
    'get_app_config', 'get_database_config', 'get_security_config'
]
