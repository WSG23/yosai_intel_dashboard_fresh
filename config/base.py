# coding: utf-8
"""Shared configuration dataclasses and transformer."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from .constants import (
    DEFAULT_APP_HOST,
    DEFAULT_APP_PORT,
    DEFAULT_CACHE_HOST,
    DEFAULT_CACHE_PORT,
    DEFAULT_DB_HOST,
    DEFAULT_DB_PORT,
)
from .dynamic_config import dynamic_config
from core.secrets_manager import SecretsManager


@dataclass
class AppConfig:
    """Application configuration."""

    title: str = "Yōsai Intel Dashboard"
    debug: bool = True
    host: str = DEFAULT_APP_HOST
    port: int = DEFAULT_APP_PORT
    secret_key: str = field(default_factory=lambda: os.getenv("SECRET_KEY", ""))
    environment: str = "development"


@dataclass
class DatabaseConfig:
    """Database configuration."""

    type: str = "sqlite"
    host: str = DEFAULT_DB_HOST
    port: int = DEFAULT_DB_PORT
    name: str = "yosai.db"
    user: str = "user"
    password: str = ""
    connection_timeout: int = 30
    initial_pool_size: int = dynamic_config.get_db_pool_size()
    max_pool_size: int = dynamic_config.get_db_pool_size() * 2
    shrink_timeout: int = 60

    def get_connection_string(self) -> str:
        """Return a database connection string."""
        if self.type == "postgresql":
            return (
                f"postgresql://{self.user}:{self.password}"
                f"@{self.host}:{self.port}/{self.name}"
            )
        if self.type == "sqlite":
            return f"sqlite:///{self.name}"
        return f"mock://{self.name}"


@dataclass
class SecurityConfig:
    """Security configuration."""

    secret_key: str = field(default_factory=lambda: os.getenv("SECRET_KEY", ""))
    session_timeout: int = 3600
    session_timeout_by_role: Dict[str, int] = field(default_factory=dict)
    cors_origins: List[str] = field(default_factory=list)
    csrf_enabled: bool = True
    max_failed_attempts: int = 5


@dataclass
class SampleFilesConfig:
    """File paths for bundled sample datasets."""

    csv_path: str = "data/sample_data.csv"
    json_path: str = "data/sample_data.json"


@dataclass
class AnalyticsConfig:
    """Analytics tuning options."""

    cache_timeout_seconds: int = 60
    max_records_per_query: int = 500000
    enable_real_time: bool = True
    batch_size: int = 25000
    chunk_size: int = 100000
    enable_chunked_analysis: bool = True
    anomaly_detection_enabled: bool = True
    ml_models_path: str = "models/ml"
    data_retention_days: int = 30
    query_timeout_seconds: int = 600
    force_full_dataset_analysis: bool = True
    max_memory_mb: int = 1024
    max_display_rows: int = 10000


@dataclass
class MonitoringConfig:
    """Runtime monitoring options."""

    health_check_enabled: bool = True
    metrics_enabled: bool = True
    health_check_interval: int = 30
    performance_monitoring: bool = False
    error_reporting_enabled: bool = True
    sentry_dsn: Optional[str] = None
    log_retention_days: int = 30


@dataclass
class CacheConfig:
    """Cache backend settings."""

    type: str = "memory"
    host: str = DEFAULT_CACHE_HOST
    port: int = DEFAULT_CACHE_PORT
    database: int = 0
    timeout_seconds: int = 300
    key_prefix: str = "yosai:"
    compression_enabled: bool = False
    max_memory_mb: int = 100


@dataclass
class SecretValidationConfig:
    """Severity configuration for secret validator."""

    severity: str = "low"


@dataclass
class Config:
    """Container for all configuration sections."""

    app: AppConfig = field(default_factory=AppConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    sample_files: SampleFilesConfig = field(default_factory=SampleFilesConfig)
    analytics: AnalyticsConfig = field(default_factory=AnalyticsConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    secret_validation: SecretValidationConfig = field(
        default_factory=SecretValidationConfig
    )
    environment: str = "development"
    plugin_settings: Dict[str, Dict[str, Any]] = field(default_factory=dict)


class ConfigTransformer:
    """Apply transformations such as environment overrides."""

    def __init__(self) -> None:
        self._callbacks: List[Callable[[Config], None]] = []
        self.register(self._apply_env_overrides)

    def register(self, func: Callable[[Config], None]) -> None:
        self._callbacks.append(func)

    def transform(self, config: Config) -> Config:
        for cb in self._callbacks:
            cb(config)
        return config

    def _apply_env_overrides(self, config: Config) -> None:
        manager = SecretsManager()

        if os.getenv("DEBUG"):
            config.app.debug = os.getenv("DEBUG").lower() in ("true", "1", "yes")
        host_env = os.getenv("HOST")
        if host_env:
            config.app.host = host_env
        port_env = os.getenv("PORT")
        if port_env:
            config.app.port = int(port_env)
        try:
            secret_env = manager.get("SECRET_KEY")
        except KeyError:
            secret_env = None
        if secret_env:
            config.app.secret_key = secret_env
            config.security.secret_key = secret_env
            os.environ.setdefault("SECRET_KEY", secret_env)
        title_env = os.getenv("APP_TITLE")
        if title_env:
            config.app.title = title_env

        # Database overrides
        db_type = os.getenv("DB_TYPE")
        if db_type:
            config.database.type = db_type
        db_host = os.getenv("DB_HOST")
        if db_host:
            config.database.host = db_host
        db_port = os.getenv("DB_PORT")
        if db_port:
            config.database.port = int(db_port)
        db_name = os.getenv("DB_NAME")
        if db_name:
            config.database.name = db_name
        db_user = os.getenv("DB_USER")
        if db_user:
            config.database.user = db_user
        try:
            db_password = manager.get("DB_PASSWORD")
        except KeyError:
            db_password = None
        if db_password:
            config.database.password = db_password
            os.environ.setdefault("DB_PASSWORD", db_password)

        config.database.initial_pool_size = dynamic_config.get_db_pool_size()
        config.database.max_pool_size = dynamic_config.get_db_pool_size() * 2
        db_timeout = os.getenv("DB_TIMEOUT")
        if db_timeout:
            config.database.connection_timeout = int(db_timeout)
        init_pool = os.getenv("DB_INITIAL_POOL_SIZE")
        if init_pool:
            config.database.initial_pool_size = int(init_pool)
        max_pool = os.getenv("DB_MAX_POOL_SIZE")
        if max_pool:
            config.database.max_pool_size = int(max_pool)
        shrink_timeout = os.getenv("DB_SHRINK_TIMEOUT")
        if shrink_timeout:
            config.database.shrink_timeout = int(shrink_timeout)

        # Security
        csrf_enabled = os.getenv("CSRF_ENABLED")
        if csrf_enabled is not None:
            config.security.csrf_enabled = csrf_enabled.lower() in ("true", "1", "yes")
        max_failed = os.getenv("MAX_FAILED_ATTEMPTS")
        if max_failed is not None:
            config.security.max_failed_attempts = int(max_failed)

        # Sample files
        sample_csv = os.getenv("SAMPLE_CSV_PATH")
        if sample_csv:
            config.sample_files.csv_path = sample_csv
        sample_json = os.getenv("SAMPLE_JSON_PATH")
        if sample_json:
            config.sample_files.json_path = sample_json

        # Cache overrides
        cache_type = os.getenv("CACHE_TYPE")
        if cache_type:
            config.cache.type = cache_type
        cache_host = os.getenv("CACHE_HOST")
        if cache_host:
            config.cache.host = cache_host
        cache_port = os.getenv("CACHE_PORT")
        if cache_port:
            config.cache.port = int(cache_port)
        cache_db = os.getenv("CACHE_DB")
        if cache_db:
            config.cache.database = int(cache_db)
        cache_timeout = os.getenv("CACHE_TIMEOUT")
        if cache_timeout:
            config.cache.timeout_seconds = int(cache_timeout)


__all__ = [
    "AppConfig",
    "DatabaseConfig",
    "SecurityConfig",
    "SampleFilesConfig",
    "AnalyticsConfig",
    "MonitoringConfig",
    "CacheConfig",
    "SecretValidationConfig",
    "Config",

    "ConfigTransformer",
]
