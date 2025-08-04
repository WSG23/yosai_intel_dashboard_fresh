"""Lightweight application settings loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class DatabaseSettings:
    """Database connection configuration."""

    host: str
    port: int
    user: str
    password: str
    name: str
    connection_timeout: Optional[int]

    @classmethod
    def from_env(cls) -> "DatabaseSettings":
        """Create settings from environment variables."""
        timeout = os.getenv("DB_TIMEOUT")
        return cls(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", ""),
            name=os.getenv("DB_NAME", "app"),
            connection_timeout=int(timeout) if timeout is not None else None,
        )


@dataclass
class SecuritySettings:
    """Security related configuration."""

    secret_key: str
    jwt_algorithm: str
    cors_origins: List[str]
    csrf_enabled: bool
    max_upload_mb: Optional[int]

    @classmethod
    def from_env(cls) -> "SecuritySettings":
        """Create settings from environment variables."""
        origins = [o for o in os.getenv("CORS_ORIGINS", "").split(",") if o]
        max_upload = os.getenv("MAX_UPLOAD_MB")
        return cls(
            secret_key=os.getenv("SECRET_KEY", "change-me"),
            jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
            cors_origins=origins,
            csrf_enabled=os.getenv("CSRF_ENABLED", "true").lower() == "true",
            max_upload_mb=int(max_upload) if max_upload is not None else None,
        )


@dataclass
class AnalyticsSettings:
    """Analytics service configuration."""

    api_key: str
    endpoint: str
    enabled: bool

    @classmethod
    def from_env(cls) -> "AnalyticsSettings":
        """Create settings from environment variables."""
        return cls(
            api_key=os.getenv("ANALYTICS_API_KEY", ""),
            endpoint=os.getenv("ANALYTICS_ENDPOINT", ""),
            enabled=os.getenv("ENABLE_ANALYTICS", "false").lower() == "true",
        )


@dataclass
class PerformanceSettings:
    """Performance tuning configuration."""

    ai_confidence_threshold: Optional[int]

    @classmethod
    def from_env(cls) -> "PerformanceSettings":
        value = os.getenv("AI_CONFIDENCE_THRESHOLD")
        return cls(ai_confidence_threshold=int(value) if value is not None else None)


@dataclass
class AppSettings:
    """Top level application configuration."""

    debug: bool
    database: DatabaseSettings
    security: SecuritySettings
    analytics: AnalyticsSettings
    performance: PerformanceSettings
    name: str = "Yōsai Intel Dashboard"

    @classmethod
    def from_env(cls) -> "AppSettings":
        """Create settings from environment variables."""
        return cls(
            debug=os.getenv("APP_DEBUG", "false").lower() == "true",
            database=DatabaseSettings.from_env(),
            security=SecuritySettings.from_env(),
            analytics=AnalyticsSettings.from_env(),
            performance=PerformanceSettings.from_env(),
            name=os.getenv("APP_NAME", "Yōsai Intel Dashboard"),
        )


class ConfigManager:
    """Manage application settings with lazy loading and reloading."""

    def __init__(self) -> None:
        self._settings: Optional[AppSettings] = None

    def get_settings(self) -> AppSettings:
        """Return loaded settings, loading them on first use."""
        if self._settings is None:
            self._settings = AppSettings.from_env()
        return self._settings

    def reload(self) -> AppSettings:
        """Force reload of settings from the environment."""
        self._settings = AppSettings.from_env()
        return self._settings


_config_manager = ConfigManager()


def get_settings(reload: bool = False) -> AppSettings:
    """Return application settings, optionally reloading them."""
    if reload:
        return _config_manager.reload()
    return _config_manager.get_settings()


__all__ = [
    "DatabaseSettings",
    "SecuritySettings",
    "AnalyticsSettings",
    "PerformanceSettings",
    "AppSettings",
    "ConfigManager",
    "get_settings",
]
