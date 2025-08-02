from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from .constants import (
    DEFAULT_APP_HOST,
    DEFAULT_APP_PORT,
    DEFAULT_CACHE_HOST,
    DEFAULT_CACHE_PORT,
    DEFAULT_DB_HOST,
    DEFAULT_DB_PORT,
)


class AppModel(BaseModel):
    title: str = "Yōsai Intel Dashboard"
    debug: bool = True
    host: str = Field(default=DEFAULT_APP_HOST, json_schema_extra={"env": "YOSAI_HOST"})
    port: int = Field(default=DEFAULT_APP_PORT, json_schema_extra={"env": "YOSAI_PORT"})
    secret_key: str = Field(..., json_schema_extra={"env": "SECRET_KEY"})
    environment: str = "development"


class DatabaseModel(BaseModel):
    type: str = "sqlite"
    host: str = Field(default=DEFAULT_DB_HOST, json_schema_extra={"env": "DB_HOST"})
    port: int = Field(default=DEFAULT_DB_PORT, json_schema_extra={"env": "DB_PORT"})
    name: str = Field(default="yosai.db", json_schema_extra={"env": "DB_NAME"})
    user: str = Field(default="user", json_schema_extra={"env": "DB_USER"})
    password: str = Field(default="", json_schema_extra={"env": "DB_PASSWORD"})
    url: str = Field(default="", json_schema_extra={"env": "DATABASE_URL"})
    connection_timeout: int = 30
    initial_pool_size: int = 10
    max_pool_size: int = 20
    async_pool_min_size: int = 10
    async_pool_max_size: int = 20
    async_connection_timeout: int = 30
    shrink_timeout: int = 60
    use_intelligent_pool: bool = False


class SecurityModel(BaseModel):
    secret_key: str = Field(
        ...,
        json_schema_extra={"env": "SECRET_KEY"},
    )
    session_timeout: int = 3600
    session_timeout_by_role: Dict[str, int] = Field(default_factory=dict)
    cors_origins: List[str] = Field(default_factory=list)
    csrf_enabled: bool = True
    max_failed_attempts: int = 5
    max_upload_mb: int = Field(default=50, json_schema_extra={"env": "MAX_UPLOAD_MB"})
    allowed_file_types: List[str] = Field(
        default_factory=lambda: [".csv", ".json", ".xlsx"]
    )


class SampleFilesModel(BaseModel):
    csv_path: str = "data/sample_data.csv"
    json_path: str = "data/sample_data.json"


class AnalyticsModel(BaseModel):
    cache_timeout_seconds: int = 60
    max_records_per_query: int = 500000
    enable_real_time: bool = True
    batch_size: int = 25000
    chunk_size: int = Field(
        default=100000, json_schema_extra={"env": "ANALYTICS_CHUNK_SIZE"}
    )
    enable_chunked_analysis: bool = True
    anomaly_detection_enabled: bool = True
    ml_models_path: str = "models/ml"
    data_retention_days: int = 30
    query_timeout_seconds: int = Field(
        default=600, json_schema_extra={"env": "QUERY_TIMEOUT_SECONDS"}
    )
    force_full_dataset_analysis: bool = True
    max_memory_mb: int = Field(
        default=500, json_schema_extra={"env": "ANALYTICS_MAX_MEMORY_MB"}
    )
    max_display_rows: int = 10000


class MonitoringModel(BaseModel):
    health_check_enabled: bool = True
    metrics_enabled: bool = True
    health_check_interval: int = 30
    performance_monitoring: bool = False
    error_reporting_enabled: bool = True
    sentry_dsn: Optional[str] = None
    log_retention_days: int = 30
    model_check_interval_minutes: int = Field(
        default=60,
        json_schema_extra={"env": "MODEL_CHECK_INTERVAL_MINUTES"},
    )
    drift_threshold_ks: float = Field(
        default=0.1,
        json_schema_extra={"env": "DRIFT_THRESHOLD_KS"},
    )
    drift_threshold_psi: float = Field(
        default=0.1,
        json_schema_extra={"env": "DRIFT_THRESHOLD_PSI"},
    )
    drift_threshold_wasserstein: float = Field(
        default=0.1,
        json_schema_extra={"env": "DRIFT_THRESHOLD_WASSERSTEIN"},
    )


class CacheModel(BaseModel):
    enabled: bool = True
    ttl: int = 3600
    max_size: int = 1000
    redis_url: Optional[str] = None
    use_memory_cache: bool = True
    use_redis: bool = False
    prefix: str = "yosai_"
    warm_keys: List[str] = Field(
        default_factory=list, json_schema_extra={"env": "CACHE_WARM_KEYS"}
    )
    host: str = Field(
        default=DEFAULT_CACHE_HOST, json_schema_extra={"env": "CACHE_HOST"}
    )
    port: int = Field(
        default=DEFAULT_CACHE_PORT, json_schema_extra={"env": "CACHE_PORT"}
    )


class UploadModel(BaseModel):
    folder: str = Field(
        default="/tmp/uploads", json_schema_extra={"env": "UPLOAD_FOLDER"}
    )
    max_file_size_mb: int = Field(
        default=16, json_schema_extra={"env": "MAX_FILE_SIZE_MB"}
    )

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024


class SecretValidationModel(BaseModel):
    severity: str = "low"


class ConfigModel(BaseModel):
    app: AppModel = Field(default_factory=AppModel)
    database: DatabaseModel = Field(default_factory=DatabaseModel)
    security: SecurityModel = Field(default_factory=SecurityModel)
    sample_files: SampleFilesModel = Field(default_factory=SampleFilesModel)
    analytics: AnalyticsModel = Field(default_factory=AnalyticsModel)
    monitoring: MonitoringModel = Field(default_factory=MonitoringModel)
    cache: CacheModel = Field(default_factory=CacheModel)
    uploads: UploadModel = Field(default_factory=UploadModel)
    secret_validation: SecretValidationModel = Field(
        default_factory=SecretValidationModel
    )
    environment: str = "development"
    plugin_settings: Dict[str, Dict[str, object]] = Field(default_factory=dict)
