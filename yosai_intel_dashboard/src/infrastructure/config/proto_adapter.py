"""Adapters between protobuf configs and existing dataclasses."""

from __future__ import annotations

from .base import (
    AnalyticsConfig,
    AppConfig,
    CacheConfig,
    Config,
    DatabaseConfig,
    MonitoringConfig,
    SampleFilesConfig,
    SecretValidationConfig,
    SecurityConfig,
    UploadConfig,
)
from .generated.protobuf.config.schema import config_pb2


def to_dataclasses(cfg: config_pb2.YosaiConfig) -> Config:
    """Convert :class:`YosaiConfig` message to existing dataclass structure."""
    app = AppConfig(
        title=cfg.app.title,
        debug=cfg.app.debug,
        host=cfg.app.host,
        port=cfg.app.port,
        secret_key=cfg.app.secret_key,
        environment=cfg.app.environment,
    )
    db = DatabaseConfig(
        type=cfg.database.type,
        host=cfg.database.host,
        port=cfg.database.port,
        name=cfg.database.name,
        user=cfg.database.user,
        password=cfg.database.password,
        url=cfg.database.url,
        connection_timeout=cfg.database.connection_timeout,
        initial_pool_size=cfg.database.initial_pool_size,
        max_pool_size=cfg.database.max_pool_size,
        async_pool_min_size=cfg.database.async_pool_min_size,
        async_pool_max_size=cfg.database.async_pool_max_size,
        async_connection_timeout=cfg.database.async_connection_timeout,
        shrink_timeout=cfg.database.shrink_timeout,
        shrink_interval=getattr(cfg.database, "shrink_interval", 0),
        use_intelligent_pool=cfg.database.use_intelligent_pool,
    )
    sec = SecurityConfig(
        secret_key=cfg.security.secret_key,
        session_timeout=cfg.security.session_timeout,
        session_timeout_by_role=dict(cfg.security.session_timeout_by_role),
        cors_origins=list(cfg.security.cors_origins),
        csrf_enabled=cfg.security.csrf_enabled,
        max_failed_attempts=cfg.security.max_failed_attempts,
        max_upload_mb=cfg.security.max_upload_mb,
        allowed_file_types=list(cfg.security.allowed_file_types),
    )
    samples = SampleFilesConfig(
        csv_path=cfg.sample_files.csv_path,
        json_path=cfg.sample_files.json_path,
    )
    analytics = AnalyticsConfig(
        cache_timeout_seconds=cfg.analytics.cache_timeout_seconds,
        max_records_per_query=cfg.analytics.max_records_per_query,
        enable_real_time=cfg.analytics.enable_real_time,
        batch_size=cfg.analytics.batch_size,
        chunk_size=cfg.analytics.chunk_size,
        enable_chunked_analysis=cfg.analytics.enable_chunked_analysis,
        anomaly_detection_enabled=cfg.analytics.anomaly_detection_enabled,
        ml_models_path=cfg.analytics.ml_models_path,
        data_retention_days=cfg.analytics.data_retention_days,
        query_timeout_seconds=cfg.analytics.query_timeout_seconds,
        force_full_dataset_analysis=cfg.analytics.force_full_dataset_analysis,
        max_memory_mb=cfg.analytics.max_memory_mb,
        max_display_rows=cfg.analytics.max_display_rows,
    )
    monitoring = MonitoringConfig(
        health_check_enabled=cfg.monitoring.health_check_enabled,
        metrics_enabled=cfg.monitoring.metrics_enabled,
        health_check_interval=cfg.monitoring.health_check_interval,
        performance_monitoring=cfg.monitoring.performance_monitoring,
        error_reporting_enabled=cfg.monitoring.error_reporting_enabled,
        sentry_dsn=cfg.monitoring.sentry_dsn,
        log_retention_days=cfg.monitoring.log_retention_days,
    )
    cache = CacheConfig(
        enabled=cfg.cache.enabled,
        ttl=cfg.cache.ttl,
        max_size=cfg.cache.max_size,
        redis_url=cfg.cache.redis_url,
        use_memory_cache=cfg.cache.use_memory_cache,
        use_redis=cfg.cache.use_redis,
        prefix=cfg.cache.prefix,
    )
    uploads = UploadConfig(
        folder=cfg.uploads.folder,
        max_file_size_mb=cfg.uploads.max_file_size_mb,
    )
    secret_validation = SecretValidationConfig(
        severity=cfg.secret_validation.severity,
    )
    return Config(
        app=app,
        database=db,
        security=sec,
        sample_files=samples,
        analytics=analytics,
        monitoring=monitoring,
        cache=cache,
        uploads=uploads,
        secret_validation=secret_validation,
        environment=cfg.environment,
    )


__all__ = ["to_dataclasses"]
