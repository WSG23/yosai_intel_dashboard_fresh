from __future__ import annotations

import warnings
from dataclasses import asdict
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, model_validator

from .app_config import UploadConfig
from .base import Config as DataclassConfig
from .base import require_env_var
from .cache_config import CacheConfig
from .constants import (
    DEFAULT_APP_HOST,
    DEFAULT_APP_PORT,
    DEFAULT_DB_HOST,
    DEFAULT_DB_PORT,
)
from .dynamic_config import dynamic_config


class AppSettings(BaseModel):
    """Application settings."""

    title: str = "Yōsai Intel Dashboard"
    debug: bool = True
    host: str = DEFAULT_APP_HOST
    port: int = DEFAULT_APP_PORT
    secret_key: str = Field(default_factory=lambda: require_env_var("SECRET_KEY"))
    environment: str = "development"


class DatabaseSettings(BaseModel):
    """Database connection settings."""

    type: str = "sqlite"
    host: str = DEFAULT_DB_HOST
    port: int = DEFAULT_DB_PORT
    name: str = "yosai.db"
    user: str = "user"
    password: str = ""
    url: str = ""
    connection_timeout: int = dynamic_config.get_db_connection_timeout()
    initial_pool_size: int = dynamic_config.get_db_pool_size()
    max_pool_size: int = dynamic_config.get_db_pool_size() * 2
    async_pool_min_size: int = dynamic_config.get_db_pool_size()
    async_pool_max_size: int = dynamic_config.get_db_pool_size() * 2
    async_connection_timeout: int = dynamic_config.get_db_connection_timeout()
    shrink_timeout: int = 60
    use_intelligent_pool: bool = False

    @model_validator(mode="after")
    def populate_url(cls, values: "DatabaseSettings") -> "DatabaseSettings":
        if not values.url:
            if values.type == "sqlite":
                values.url = f"sqlite:///{values.name}"
            elif values.type == "postgresql":
                if values.user and values.password:
                    values.url = (
                        f"postgresql://{values.user}:{values.password}"
                        f"@{values.host}:{values.port}/{values.name}"
                    )
                else:
                    values.url = (
                        f"postgresql://{values.host}:{values.port}/{values.name}"
                    )
            elif values.type == "mysql":
                if values.user and values.password:
                    values.url = (
                        f"mysql://{values.user}:{values.password}"
                        f"@{values.host}:{values.port}/{values.name}"
                    )
                else:
                    values.url = f"mysql://{values.host}:{values.port}/{values.name}"
        return values

    def get_connection_string(self) -> str:  # pragma: no cover - util
        if self.type == "postgresql":
            return (
                f"postgresql://{self.user}:{self.password}"
                f"@{self.host}:{self.port}/{self.name}"
            )
        if self.type == "sqlite":
            return f"sqlite:///{self.name}"
        return f"mock://{self.name}"


class SecuritySettings(BaseModel):
    """Security related settings."""

    secret_key: str = Field(default_factory=lambda: require_env_var("SECRET_KEY"))
    session_timeout: int = 3600
    session_timeout_by_role: Dict[str, int] = Field(default_factory=dict)
    cors_origins: List[str] = Field(default_factory=list)
    csrf_enabled: bool = True
    max_failed_attempts: int = 5
    max_upload_mb: int = 50
    allowed_file_types: List[str] = Field(
        default_factory=lambda: [".csv", ".json", ".xlsx"]
    )
    max_file_size_bytes: int = 0

    @model_validator(mode="after")
    def compute_file_size(cls, values: "SecuritySettings") -> "SecuritySettings":
        values.max_file_size_bytes = values.max_upload_mb * 1024 * 1024
        return values


class SampleFilesSettings(BaseModel):
    csv_path: str = "data/sample_data.csv"
    json_path: str = "data/sample_data.json"


class AnalyticsSettings(BaseModel):
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
    max_memory_mb: int = 500
    max_display_rows: int = 10000

    @model_validator(mode="after")
    def clamp_memory(cls, values: "AnalyticsSettings") -> "AnalyticsSettings":
        if values.max_memory_mb > 500:
            warnings.warn(
                ("max_memory_mb %s exceeds security limit of 500 MB; clamping to 500")
                % values.max_memory_mb,
                RuntimeWarning,
                stacklevel=2,
            )
            values.max_memory_mb = 500
        return values


class MonitoringSettings(BaseModel):
    health_check_enabled: bool = True
    metrics_enabled: bool = True
    health_check_interval: int = 30
    performance_monitoring: bool = False
    error_reporting_enabled: bool = True
    sentry_dsn: Optional[str] = None
    log_retention_days: int = 30
    model_evaluation_interval: int = 60
    model_check_interval_minutes: int = 60
    drift_threshold_ks: float = 0.1
    drift_threshold_psi: float = 0.1
    drift_threshold_wasserstein: float = 0.1


class DataQualityThresholds(BaseModel):
    max_missing_ratio: float = 0.1
    max_outlier_ratio: float = 0.01
    max_schema_violations: int = 0
    max_avro_decode_failures: int = 0
    max_compatibility_failures: int = 0


class SecretValidationSettings(BaseModel):
    severity: str = "low"


class ConfigSchema(BaseModel):
    app: AppSettings = Field(default_factory=AppSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    sample_files: SampleFilesSettings = Field(default_factory=SampleFilesSettings)
    analytics: AnalyticsSettings = Field(default_factory=AnalyticsSettings)
    monitoring: MonitoringSettings = Field(default_factory=MonitoringSettings)
    data_quality: DataQualityThresholds = Field(default_factory=DataQualityThresholds)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    uploads: UploadConfig = Field(default_factory=UploadConfig)
    secret_validation: SecretValidationSettings = Field(
        default_factory=SecretValidationSettings
    )
    environment: str = "development"
    plugin_settings: Dict[str, Dict[str, Any]] = Field(default_factory=dict)

    @classmethod
    def from_dataclass(cls, cfg: DataclassConfig) -> "ConfigSchema":
        return cls.model_validate(asdict(cfg))


__all__ = [
    "AppSettings",
    "DatabaseSettings",
    "SecuritySettings",
    "SampleFilesSettings",
    "AnalyticsSettings",
    "MonitoringSettings",
    "DataQualityThresholds",
    "SecretValidationSettings",
    "ConfigSchema",
]
