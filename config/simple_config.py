"""
Simplified configuration management
"""
import os
from dataclasses import dataclass
from typing import Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class Config:
    """Single configuration class with sensible defaults"""
    debug: bool = False
    host: str = "127.0.0.1"
    port: int = 8050
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "yosai_intel"
    db_user: str = "postgres"
    db_password: str = ""
    db_type: str = "mock"
    secret_key: str = "dev-key-change-for-production"
    csrf_enabled: bool = True

    @classmethod
    def from_environment(cls) -> 'Config':
        """Create config from environment variables"""
        return cls(
            debug=os.getenv('DEBUG', 'false').lower() == 'true',
            host=os.getenv('HOST', '127.0.0.1'),
            port=int(os.getenv('PORT', '8050')),
            db_host=os.getenv('DB_HOST', 'localhost'),
            db_port=int(os.getenv('DB_PORT', '5432')),
            db_name=os.getenv('DB_NAME', 'yosai_intel'),
            db_user=os.getenv('DB_USER', 'postgres'),
            db_password=os.getenv('DB_PASSWORD', ''),
            db_type=os.getenv('DB_TYPE', 'mock'),
            secret_key=os.getenv('SECRET_KEY', 'dev-key-change-for-production'),
            csrf_enabled=os.getenv('CSRF_ENABLED', 'true').lower() == 'true'
        )

    def validate(self) -> list[str]:
        """Validate configuration and return warnings"""
        warnings = []
        if self.secret_key == "dev-key-change-for-production":
            warnings.append("Using default secret key - change for production")
        if self.debug and self.host == "0.0.0.0":
            warnings.append("Debug mode with host 0.0.0.0 is a security risk")
        if self.db_type == "postgresql" and not self.db_password:
            warnings.append("PostgreSQL requires a password")
        return warnings


_config: Optional[Config] = None


def get_config() -> Config:
    """Get global configuration"""
    global _config
    if _config is None:
        _config = Config.from_environment()
        warnings = _config.validate()
        for warning in warnings:
            logger.warning(warning)
    return _config
