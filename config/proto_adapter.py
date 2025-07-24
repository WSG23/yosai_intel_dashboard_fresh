"""Adapters between protobuf configs and existing dataclasses."""
from __future__ import annotations

from .generated.protobuf.config.schema import config_pb2
from .base import AppConfig, DatabaseConfig, SecurityConfig, Config


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
    return Config(app=app, database=db, security=sec, environment=cfg.environment)


__all__ = ["to_dataclasses"]
