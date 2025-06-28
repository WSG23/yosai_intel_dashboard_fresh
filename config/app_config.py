"""Immutable configuration objects using dataclasses"""
from dataclasses import dataclass, field
from typing import Dict, Any, List

@dataclass(frozen=True)
class DatabaseConfig:
    """Immutable database configuration"""
    host: str = "localhost"
    port: int = 5432
    name: str = "yosai_intel"
    username: str = "postgres"
    password: str = ""
    connection_pool_size: int = 10
    connection_timeout: int = 30

    @property
    def connection_string(self) -> str:
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.name}"

@dataclass(frozen=True)
class SecurityConfig:
    """Immutable security configuration"""
    secret_key: str = "change-me-in-production"
    csrf_enabled: bool = True
    session_timeout: int = 3600
    max_failed_attempts: int = 5

@dataclass(frozen=True)
class AppConfig:
    """Main application configuration"""
    title: str = "Yōsai Intel Dashboard"
    debug: bool = False
    host: str = "127.0.0.1"
    port: int = 8050
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)

    def validate(self) -> List[str]:
        issues: List[str] = []
        if self.security.secret_key == "change-me-in-production":
            issues.append("SECRET_KEY should be changed for production")
        if self.debug and self.host != "127.0.0.1":
            issues.append("Debug mode should not be enabled on non-localhost")
        return issues
