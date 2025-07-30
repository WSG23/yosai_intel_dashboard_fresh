from typing import ClassVar as _ClassVar
from typing import Iterable as _Iterable
from typing import Mapping as _Mapping
from typing import Optional as _Optional
from typing import Union as _Union

from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf.internal import containers as _containers

DESCRIPTOR: _descriptor.FileDescriptor

class AnalyticsConfig(_message.Message):
    __slots__ = [
        "anomaly_detection_enabled",
        "batch_size",
        "cache_timeout_seconds",
        "chunk_size",
        "data_retention_days",
        "enable_chunked_analysis",
        "enable_real_time",
        "force_full_dataset_analysis",
        "max_display_rows",
        "max_memory_mb",
        "max_records_per_query",
        "ml_models_path",
        "query_timeout_seconds",
    ]
    ANOMALY_DETECTION_ENABLED_FIELD_NUMBER: _ClassVar[int]
    BATCH_SIZE_FIELD_NUMBER: _ClassVar[int]
    CACHE_TIMEOUT_SECONDS_FIELD_NUMBER: _ClassVar[int]
    CHUNK_SIZE_FIELD_NUMBER: _ClassVar[int]
    DATA_RETENTION_DAYS_FIELD_NUMBER: _ClassVar[int]
    ENABLE_CHUNKED_ANALYSIS_FIELD_NUMBER: _ClassVar[int]
    ENABLE_REAL_TIME_FIELD_NUMBER: _ClassVar[int]
    FORCE_FULL_DATASET_ANALYSIS_FIELD_NUMBER: _ClassVar[int]
    MAX_DISPLAY_ROWS_FIELD_NUMBER: _ClassVar[int]
    MAX_MEMORY_MB_FIELD_NUMBER: _ClassVar[int]
    MAX_RECORDS_PER_QUERY_FIELD_NUMBER: _ClassVar[int]
    ML_MODELS_PATH_FIELD_NUMBER: _ClassVar[int]
    QUERY_TIMEOUT_SECONDS_FIELD_NUMBER: _ClassVar[int]
    anomaly_detection_enabled: bool
    batch_size: int
    cache_timeout_seconds: int
    chunk_size: int
    data_retention_days: int
    enable_chunked_analysis: bool
    enable_real_time: bool
    force_full_dataset_analysis: bool
    max_display_rows: int
    max_memory_mb: int
    max_records_per_query: int
    ml_models_path: str
    query_timeout_seconds: int
    def __init__(
        self,
        cache_timeout_seconds: _Optional[int] = ...,
        max_records_per_query: _Optional[int] = ...,
        enable_real_time: bool = ...,
        batch_size: _Optional[int] = ...,
        chunk_size: _Optional[int] = ...,
        enable_chunked_analysis: bool = ...,
        anomaly_detection_enabled: bool = ...,
        ml_models_path: _Optional[str] = ...,
        data_retention_days: _Optional[int] = ...,
        query_timeout_seconds: _Optional[int] = ...,
        force_full_dataset_analysis: bool = ...,
        max_memory_mb: _Optional[int] = ...,
        max_display_rows: _Optional[int] = ...,
    ) -> None: ...

class AppConfig(_message.Message):
    __slots__ = ["debug", "environment", "host", "port", "secret_key", "title"]
    DEBUG_FIELD_NUMBER: _ClassVar[int]
    ENVIRONMENT_FIELD_NUMBER: _ClassVar[int]
    HOST_FIELD_NUMBER: _ClassVar[int]
    PORT_FIELD_NUMBER: _ClassVar[int]
    SECRET_KEY_FIELD_NUMBER: _ClassVar[int]
    TITLE_FIELD_NUMBER: _ClassVar[int]
    debug: bool
    environment: str
    host: str
    port: int
    secret_key: str
    title: str
    def __init__(
        self,
        title: _Optional[str] = ...,
        debug: bool = ...,
        host: _Optional[str] = ...,
        port: _Optional[int] = ...,
        secret_key: _Optional[str] = ...,
        environment: _Optional[str] = ...,
    ) -> None: ...

class CacheConfig(_message.Message):
    __slots__ = [
        "enabled",
        "max_size",
        "prefix",
        "redis_url",
        "ttl",
        "use_memory_cache",
        "use_redis",
    ]
    ENABLED_FIELD_NUMBER: _ClassVar[int]
    MAX_SIZE_FIELD_NUMBER: _ClassVar[int]
    PREFIX_FIELD_NUMBER: _ClassVar[int]
    REDIS_URL_FIELD_NUMBER: _ClassVar[int]
    TTL_FIELD_NUMBER: _ClassVar[int]
    USE_MEMORY_CACHE_FIELD_NUMBER: _ClassVar[int]
    USE_REDIS_FIELD_NUMBER: _ClassVar[int]
    enabled: bool
    max_size: int
    prefix: str
    redis_url: str
    ttl: int
    use_memory_cache: bool
    use_redis: bool
    def __init__(
        self,
        enabled: bool = ...,
        ttl: _Optional[int] = ...,
        max_size: _Optional[int] = ...,
        redis_url: _Optional[str] = ...,
        use_memory_cache: bool = ...,
        use_redis: bool = ...,
        prefix: _Optional[str] = ...,
    ) -> None: ...

class DatabaseConfig(_message.Message):
    __slots__ = [
        "async_connection_timeout",
        "async_pool_max_size",
        "async_pool_min_size",
        "connection_timeout",
        "host",
        "initial_pool_size",
        "max_pool_size",
        "name",
        "password",
        "port",
        "shrink_timeout",
        "type",
        "url",
        "use_intelligent_pool",
        "user",
    ]
    ASYNC_CONNECTION_TIMEOUT_FIELD_NUMBER: _ClassVar[int]
    ASYNC_POOL_MAX_SIZE_FIELD_NUMBER: _ClassVar[int]
    ASYNC_POOL_MIN_SIZE_FIELD_NUMBER: _ClassVar[int]
    CONNECTION_TIMEOUT_FIELD_NUMBER: _ClassVar[int]
    HOST_FIELD_NUMBER: _ClassVar[int]
    INITIAL_POOL_SIZE_FIELD_NUMBER: _ClassVar[int]
    MAX_POOL_SIZE_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    PASSWORD_FIELD_NUMBER: _ClassVar[int]
    PORT_FIELD_NUMBER: _ClassVar[int]
    SHRINK_TIMEOUT_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    URL_FIELD_NUMBER: _ClassVar[int]
    USER_FIELD_NUMBER: _ClassVar[int]
    USE_INTELLIGENT_POOL_FIELD_NUMBER: _ClassVar[int]
    async_connection_timeout: int
    async_pool_max_size: int
    async_pool_min_size: int
    connection_timeout: int
    host: str
    initial_pool_size: int
    max_pool_size: int
    name: str
    password: str
    port: int
    shrink_timeout: int
    type: str
    url: str
    use_intelligent_pool: bool
    user: str
    def __init__(
        self,
        type: _Optional[str] = ...,
        host: _Optional[str] = ...,
        port: _Optional[int] = ...,
        name: _Optional[str] = ...,
        user: _Optional[str] = ...,
        password: _Optional[str] = ...,
        url: _Optional[str] = ...,
        connection_timeout: _Optional[int] = ...,
        initial_pool_size: _Optional[int] = ...,
        max_pool_size: _Optional[int] = ...,
        async_pool_min_size: _Optional[int] = ...,
        async_pool_max_size: _Optional[int] = ...,
        async_connection_timeout: _Optional[int] = ...,
        shrink_timeout: _Optional[int] = ...,
        use_intelligent_pool: bool = ...,
    ) -> None: ...

class MonitoringConfig(_message.Message):
    __slots__ = [
        "error_reporting_enabled",
        "health_check_enabled",
        "health_check_interval",
        "log_retention_days",
        "metrics_enabled",
        "performance_monitoring",
        "sentry_dsn",
    ]
    ERROR_REPORTING_ENABLED_FIELD_NUMBER: _ClassVar[int]
    HEALTH_CHECK_ENABLED_FIELD_NUMBER: _ClassVar[int]
    HEALTH_CHECK_INTERVAL_FIELD_NUMBER: _ClassVar[int]
    LOG_RETENTION_DAYS_FIELD_NUMBER: _ClassVar[int]
    METRICS_ENABLED_FIELD_NUMBER: _ClassVar[int]
    PERFORMANCE_MONITORING_FIELD_NUMBER: _ClassVar[int]
    SENTRY_DSN_FIELD_NUMBER: _ClassVar[int]
    error_reporting_enabled: bool
    health_check_enabled: bool
    health_check_interval: int
    log_retention_days: int
    metrics_enabled: bool
    performance_monitoring: bool
    sentry_dsn: str
    def __init__(
        self,
        health_check_enabled: bool = ...,
        metrics_enabled: bool = ...,
        health_check_interval: _Optional[int] = ...,
        performance_monitoring: bool = ...,
        error_reporting_enabled: bool = ...,
        sentry_dsn: _Optional[str] = ...,
        log_retention_days: _Optional[int] = ...,
    ) -> None: ...

class SampleFilesConfig(_message.Message):
    __slots__ = ["csv_path", "json_path"]
    CSV_PATH_FIELD_NUMBER: _ClassVar[int]
    JSON_PATH_FIELD_NUMBER: _ClassVar[int]
    csv_path: str
    json_path: str
    def __init__(
        self, csv_path: _Optional[str] = ..., json_path: _Optional[str] = ...
    ) -> None: ...

class SecretValidationConfig(_message.Message):
    __slots__ = ["severity"]
    SEVERITY_FIELD_NUMBER: _ClassVar[int]
    severity: str
    def __init__(self, severity: _Optional[str] = ...) -> None: ...

class SecurityConfig(_message.Message):
    __slots__ = [
        "allowed_file_types",
        "cors_origins",
        "csrf_enabled",
        "max_failed_attempts",
        "max_upload_mb",
        "secret_key",
        "session_timeout",
        "session_timeout_by_role",
    ]

    class SessionTimeoutByRoleEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: int
        def __init__(
            self, key: _Optional[str] = ..., value: _Optional[int] = ...
        ) -> None: ...

    ALLOWED_FILE_TYPES_FIELD_NUMBER: _ClassVar[int]
    CORS_ORIGINS_FIELD_NUMBER: _ClassVar[int]
    CSRF_ENABLED_FIELD_NUMBER: _ClassVar[int]
    MAX_FAILED_ATTEMPTS_FIELD_NUMBER: _ClassVar[int]
    MAX_UPLOAD_MB_FIELD_NUMBER: _ClassVar[int]
    SECRET_KEY_FIELD_NUMBER: _ClassVar[int]
    SESSION_TIMEOUT_BY_ROLE_FIELD_NUMBER: _ClassVar[int]
    SESSION_TIMEOUT_FIELD_NUMBER: _ClassVar[int]
    allowed_file_types: _containers.RepeatedScalarFieldContainer[str]
    cors_origins: _containers.RepeatedScalarFieldContainer[str]
    csrf_enabled: bool
    max_failed_attempts: int
    max_upload_mb: int
    secret_key: str
    session_timeout: int
    session_timeout_by_role: _containers.ScalarMap[str, int]
    def __init__(
        self,
        secret_key: _Optional[str] = ...,
        session_timeout: _Optional[int] = ...,
        session_timeout_by_role: _Optional[_Mapping[str, int]] = ...,
        cors_origins: _Optional[_Iterable[str]] = ...,
        csrf_enabled: bool = ...,
        max_failed_attempts: _Optional[int] = ...,
        max_upload_mb: _Optional[int] = ...,
        allowed_file_types: _Optional[_Iterable[str]] = ...,
    ) -> None: ...

class UploadConfig(_message.Message):
    __slots__ = ["folder", "max_file_size_mb"]
    FOLDER_FIELD_NUMBER: _ClassVar[int]
    MAX_FILE_SIZE_MB_FIELD_NUMBER: _ClassVar[int]
    folder: str
    max_file_size_mb: int
    def __init__(
        self, folder: _Optional[str] = ..., max_file_size_mb: _Optional[int] = ...
    ) -> None: ...

class YosaiConfig(_message.Message):
    __slots__ = [
        "analytics",
        "app",
        "cache",
        "database",
        "environment",
        "monitoring",
        "sample_files",
        "secret_validation",
        "security",
        "uploads",
    ]
    ANALYTICS_FIELD_NUMBER: _ClassVar[int]
    APP_FIELD_NUMBER: _ClassVar[int]
    CACHE_FIELD_NUMBER: _ClassVar[int]
    DATABASE_FIELD_NUMBER: _ClassVar[int]
    ENVIRONMENT_FIELD_NUMBER: _ClassVar[int]
    MONITORING_FIELD_NUMBER: _ClassVar[int]
    SAMPLE_FILES_FIELD_NUMBER: _ClassVar[int]
    SECRET_VALIDATION_FIELD_NUMBER: _ClassVar[int]
    SECURITY_FIELD_NUMBER: _ClassVar[int]
    UPLOADS_FIELD_NUMBER: _ClassVar[int]
    analytics: AnalyticsConfig
    app: AppConfig
    cache: CacheConfig
    database: DatabaseConfig
    environment: str
    monitoring: MonitoringConfig
    sample_files: SampleFilesConfig
    secret_validation: SecretValidationConfig
    security: SecurityConfig
    uploads: UploadConfig
    def __init__(
        self,
        app: _Optional[_Union[AppConfig, _Mapping]] = ...,
        database: _Optional[_Union[DatabaseConfig, _Mapping]] = ...,
        security: _Optional[_Union[SecurityConfig, _Mapping]] = ...,
        sample_files: _Optional[_Union[SampleFilesConfig, _Mapping]] = ...,
        analytics: _Optional[_Union[AnalyticsConfig, _Mapping]] = ...,
        monitoring: _Optional[_Union[MonitoringConfig, _Mapping]] = ...,
        cache: _Optional[_Union[CacheConfig, _Mapping]] = ...,
        uploads: _Optional[_Union[UploadConfig, _Mapping]] = ...,
        secret_validation: _Optional[_Union[SecretValidationConfig, _Mapping]] = ...,
        environment: _Optional[str] = ...,
    ) -> None: ...
