# coding: utf-8
"""Shared configuration dataclasses and transformer."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .app_config import UploadConfig
from .constants import (
    DEFAULT_APP_HOST,
    DEFAULT_APP_PORT,
    DEFAULT_CACHE_HOST,
    DEFAULT_CACHE_PORT,
    DEFAULT_DB_HOST,
    DEFAULT_DB_PORT,
)
from .dynamic_config import dynamic_config


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
    # Database connection URL. If empty, generated from other fields.
    url: str = ""
    connection_timeout: int = dynamic_config.get_db_connection_timeout()
    initial_pool_size: int = dynamic_config.get_db_pool_size()
    max_pool_size: int = dynamic_config.get_db_pool_size() * 2
    shrink_timeout: int = 60

    def __post_init__(self) -> None:
        """Auto-generate connection URL if not explicitly provided."""
        if not self.url:
            if self.type == "sqlite":
                self.url = f"sqlite:///{self.name}"
            elif self.type == "postgresql":
                if self.user and self.password:
                    self.url = (
                        f"postgresql://{self.user}:{self.password}"
                        f"@{self.host}:{self.port}/{self.name}"
                    )
                else:
                    self.url = f"postgresql://{self.host}:{self.port}/{self.name}"
            elif self.type == "mysql":
                if self.user and self.password:
                    self.url = (
                        f"mysql://{self.user}:{self.password}"
                        f"@{self.host}:{self.port}/{self.name}"
                    )
                else:
                    self.url = f"mysql://{self.host}:{self.port}/{self.name}"

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
    max_upload_mb: int = 50
    allowed_file_types: List[str] = field(
        default_factory=lambda: [".csv", ".json", ".xlsx"]
    )
    max_file_size_bytes: int = field(init=False)

    def __post_init__(self) -> None:
        self.max_file_size_bytes = self.max_upload_mb * 1024 * 1024


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
    uploads: UploadConfig = field(default_factory=UploadConfig)
    secret_validation: SecretValidationConfig = field(
        default_factory=SecretValidationConfig
    )
    environment: str = "development"
    plugin_settings: Dict[str, Dict[str, Any]] = field(default_factory=dict)


__all__ = [
    "AppConfig",
    "DatabaseConfig",
    "SecurityConfig",
    "SampleFilesConfig",
    "AnalyticsConfig",
    "MonitoringConfig",
    "CacheConfig",
    "UploadConfig",
    "SecretValidationConfig",
    "Config",
]
