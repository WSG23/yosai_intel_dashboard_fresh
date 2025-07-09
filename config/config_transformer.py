"""Configuration transformation utilities."""
from __future__ import annotations

import os
from typing import Callable, List

from .base_config import Config
from .dynamic_config import dynamic_config
from core.secrets_manager import SecretsManager


class ConfigTransformer:
    """Apply transformations such as environment overrides."""

    def __init__(self) -> None:
        self._callbacks: List[Callable[[Config], None]] = []
        # Register default env override callback
        self.register(self._apply_env_overrides)

    # ------------------------------------------------------------------
    def register(self, func: Callable[[Config], None]) -> None:
        self._callbacks.append(func)

    def transform(self, config: Config) -> Config:
        for cb in self._callbacks:
            cb(config)
        return config

    # ------------------------------------------------------------------
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


__all__ = ["ConfigTransformer"]

