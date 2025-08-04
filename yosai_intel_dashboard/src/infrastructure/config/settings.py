"""Application settings read from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class DatabaseSettings:
    """Database connection configuration."""

    host: str = field(default_factory=lambda: os.getenv("DB_HOST", "localhost"))
    port: int = field(default_factory=lambda: int(os.getenv("DB_PORT", "5432")))
    user: str = field(default_factory=lambda: os.getenv("DB_USER", "postgres"))
    password: str = field(default_factory=lambda: os.getenv("DB_PASSWORD", ""))
    name: str = field(default_factory=lambda: os.getenv("DB_NAME", "app"))
    min_connections: int = field(
        default_factory=lambda: int(os.getenv("DB_MIN_CONNECTIONS", "1"))
    )
    max_connections: int = field(
        default_factory=lambda: int(os.getenv("DB_MAX_CONNECTIONS", "10"))
    )
    timeout: float = field(default_factory=lambda: float(os.getenv("DB_TIMEOUT", "30")))


@dataclass
class SecuritySettings:
    """Security related configuration."""

    secret_key: str = field(
        default_factory=lambda: os.getenv("SECRET_KEY", "change-me")
    )
    jwt_algorithm: str = field(
        default_factory=lambda: os.getenv("JWT_ALGORITHM", "HS256")
    )
    cors_origins: List[str] = field(
        default_factory=lambda: [
            o for o in os.getenv("CORS_ORIGINS", "").split(",") if o
        ]
    )
    csrf_enabled: bool = field(
        default_factory=lambda: os.getenv("CSRF_ENABLED", "true").lower() == "true"
    )


@dataclass
class AnalyticsSettings:
    """Analytics service configuration."""

    api_key: str = field(default_factory=lambda: os.getenv("ANALYTICS_API_KEY", ""))
    endpoint: str = field(default_factory=lambda: os.getenv("ANALYTICS_ENDPOINT", ""))
    enabled: bool = field(
        default_factory=lambda: os.getenv("ENABLE_ANALYTICS", "false").lower() == "true"
    )


@dataclass
class AppSettings:
    """Top level application configuration."""

    debug: bool = field(
        default_factory=lambda: os.getenv("APP_DEBUG", "false").lower() == "true"
    )
    database: DatabaseSettings = field(default_factory=DatabaseSettings)
    security: SecuritySettings = field(default_factory=SecuritySettings)
    analytics: AnalyticsSettings = field(default_factory=AnalyticsSettings)
    name: str = field(
        default_factory=lambda: os.getenv("APP_NAME", "Yōsai Intel Dashboard")
    )


class ConfigManager:
    """Manage application settings with optional ``.env`` loading."""

    def __init__(self, env_file: Optional[str] = None) -> None:
        self._settings: Optional[AppSettings] = None
        self._load_env(env_file)

    @staticmethod
    def _load_env(env_file: Optional[str]) -> None:
        """Load environment variables from a ``.env`` file if available."""
        try:
            from dotenv import load_dotenv  # type: ignore import-not-found

            if env_file:
                load_dotenv(env_file, override=True)
            else:
                load_dotenv(override=True)
        except Exception:
            # ``python-dotenv`` is optional; ignore if not installed.
            pass

    def get_settings(self, reload: bool = False) -> AppSettings:
        """Return loaded settings, reloading them if requested."""
        if self._settings is None or reload:
            self._settings = AppSettings()
        return self._settings


_config_manager = ConfigManager()


def get_settings(reload: bool = False) -> AppSettings:
    """Return application settings using the global ``ConfigManager`` instance."""
    return _config_manager.get_settings(reload=reload)


__all__ = [
    "DatabaseSettings",
    "SecuritySettings",
    "AnalyticsSettings",
    "AppSettings",
    "ConfigManager",
    "get_settings",
]
