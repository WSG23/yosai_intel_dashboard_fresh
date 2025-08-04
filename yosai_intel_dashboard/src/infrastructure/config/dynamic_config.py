from __future__ import annotations

import logging
import os
import re
from typing import Any, Dict

from .app_config import UploadConfig
from .base_loader import BaseConfigLoader
from .constants import (
    AnalyticsConstants,
    CSSConstants,
    DatabaseConstants,
    PerformanceConstants,
    RateLimitConfig,
    SecurityConstants,
    StreamingConstants,
    UploadLimits,
)
from .environment import select_config_file
from yosai_intel_dashboard.src.infrastructure.config.configuration_mixin import (
    ConfigurationMixin,
)

logger = logging.getLogger(__name__)


class DynamicConfigManager(ConfigurationMixin, BaseConfigLoader):
    """Loads constants and applies environment overrides."""

    def __init__(self) -> None:
        self.security = SecurityConstants()
        self.performance = PerformanceConstants()
        self.css = CSSConstants()
        self.analytics = AnalyticsConstants()
        self.database = DatabaseConstants()
        self.streaming = StreamingConstants()
        self.uploads = UploadLimits()
        self.upload = UploadConfig()
        self._load_yaml_config()
        self._apply_env_overrides()

    def _load_yaml_config(self) -> None:
        """Load configuration from YAML files."""
        try:
            config_path = select_config_file()

            if config_path and config_path.exists():
                config_data = self.load_file(config_path)

                analytics_config = config_data.get("analytics", {})
                for key, value in analytics_config.items():
                    if hasattr(self.analytics, key) and isinstance(
                        value, type(getattr(self.analytics, key))
                    ):
                        setattr(self.analytics, key, value)
                    else:
                        logger.warning(
                            "Invalid analytics config for %s: %r", key, value
                        )

                uploads_config = config_data.get("uploads", {})
                key_map = {
                    "chunk_size": "DEFAULT_CHUNK_SIZE",
                    "max_parallel_uploads": "MAX_PARALLEL_UPLOADS",
                    "validator_rules": "VALIDATOR_RULES",
                }
                for key, value in uploads_config.items():
                    attr = key_map.get(key, key)
                    if hasattr(self.uploads, attr) and isinstance(
                        value, type(getattr(self.uploads, attr))
                    ):
                        setattr(self.uploads, attr, value)
                    else:
                        logger.warning("Invalid uploads config for %s", key)

                streaming_config = config_data.get("streaming", {})
                for key, value in streaming_config.items():
                    if hasattr(self.streaming, key) and isinstance(
                        value, type(getattr(self.streaming, key))
                    ):
                        setattr(self.streaming, key, value)
                    else:
                        logger.warning("Invalid streaming config for %s", key)

                database_config = config_data.get("database", {})
                if "connection_timeout" in database_config:
                    value = database_config["connection_timeout"]
                    if isinstance(value, int):
                        self.database.connection_timeout_seconds = value
                    else:
                        logger.warning("Invalid database connection_timeout: %r", value)

                security_config = config_data.get("security", {})
                rate_limits_cfg = security_config.get("rate_limits", {})
                for tier, values in rate_limits_cfg.items():
                    if not isinstance(values, dict):
                        logger.warning("Invalid rate limit config for %s", tier)
                        continue
                    self.security.rate_limits[tier] = RateLimitConfig(
                        int(values.get("requests", self.security.rate_limit_requests)),
                        int(
                            values.get(
                                "window_minutes",
                                self.security.rate_limit_window_minutes,
                            )
                        ),
                        int(values.get("burst", 0)),
                    )

        except Exception as exc:
            logging.getLogger(__name__).warning(
                "Failed to load %s: %s", config_path, exc
            )

    def _apply_env_overrides(self) -> None:
        """Override defaults from environment variables with validation."""
        iterations = os.getenv("PBKDF2_ITERATIONS")
        if iterations is not None:
            self.security.pbkdf2_iterations = int(iterations)

        requests_limit = os.getenv("RATE_LIMIT_REQUESTS")
        if requests_limit is None:
            requests_limit = os.getenv("RATE_LIMIT_API")
        if requests_limit is not None:
            self.security.rate_limit_requests = int(requests_limit)
            self.security.rate_limits.setdefault(
                "default",
                RateLimitConfig(self.security.rate_limit_requests, self.security.rate_limit_window_minutes, 0),
            ).requests = int(requests_limit)

        rate_limit_window = os.getenv("RATE_LIMIT_WINDOW")
        if rate_limit_window is not None:
            self.security.rate_limit_window_minutes = int(rate_limit_window)
            self.security.rate_limits.setdefault(
                "default",
                RateLimitConfig(self.security.rate_limit_requests, self.security.rate_limit_window_minutes, 0),
            ).window_minutes = int(rate_limit_window)

        max_upload = os.getenv("MAX_UPLOAD_MB")
        if max_upload is not None:
            value = int(max_upload)
            if value < 50:  # Prevent accidentally setting too small
                logger.warning(
                    "MAX_UPLOAD_MB=%s is too small. Using 50MB minimum.",
                    value,
                )
                value = 50
            elif value > 500:
                logger.warning(
                    "MAX_UPLOAD_MB=%s is too large. Using 500MB maximum.",
                    value,
                )
                value = 500
            self.security.max_upload_mb = value
            self.security.max_file_size_mb = value  # Keep them in sync

        db_pool = os.getenv("DB_POOL_SIZE")
        if db_pool is not None:
            self.performance.db_pool_size = int(db_pool)

        ai_threshold = os.getenv("AI_CONFIDENCE_THRESHOLD")
        if ai_threshold is not None:
            self.performance.ai_confidence_threshold = int(ai_threshold)

        profiling_enabled = os.getenv("PERFORMANCE_PROFILING_ENABLED")
        if profiling_enabled is not None:
            self.performance.profiling_enabled = profiling_enabled.lower() in (
                "1",
                "true",
                "yes",
            )

        mem_thresh = os.getenv("MEMORY_THRESHOLD_MB")
        if mem_thresh is not None:
            value = int(mem_thresh)
            if value > 500:
                logger.warning(
                    "MEMORY_THRESHOLD_MB=%s is too high. Using 500MB maximum.",
                    value,
                )
                value = 500
            self.performance.memory_usage_threshold_mb = value

        db_timeout = os.getenv("DB_TIMEOUT")
        if db_timeout is not None:
            self.database.connection_timeout_seconds = int(db_timeout)

        css_threshold = os.getenv("CSS_BUNDLE_THRESHOLD")
        if css_threshold is not None:
            self.css.bundle_threshold_kb = int(css_threshold)

        css_specificity = os.getenv("CSS_SPECIFICITY_HIGH")
        if css_specificity is not None:
            self.css.specificity_high = int(css_specificity)

        analytics_cache = os.getenv("ANALYTICS_CACHE_TIMEOUT")
        if analytics_cache is not None:
            self.analytics.cache_timeout_seconds = int(analytics_cache)

        chunk_size = os.getenv("ANALYTICS_CHUNK_SIZE")
        if chunk_size is not None:
            self.analytics.chunk_size = int(chunk_size)

        min_chunk_size = os.getenv("ANALYTICS_MIN_CHUNK_SIZE")
        if min_chunk_size is not None:
            self.analytics.min_chunk_size = int(min_chunk_size)

        batch_size = os.getenv("ANALYTICS_BATCH_SIZE")
        if batch_size is not None:
            self.analytics.batch_size = int(batch_size)

        max_memory = os.getenv("ANALYTICS_MAX_MEMORY_MB")
        if max_memory is not None:
            value = int(max_memory)
            if value > 500:
                logger.warning(
                    "ANALYTICS_MAX_MEMORY_MB=%s is too high. Using 500MB maximum.",
                    value,
                )
                value = 500
            self.analytics.max_memory_mb = value

        max_workers = os.getenv("ANALYTICS_MAX_WORKERS")
        if max_workers is not None:
            self.analytics.max_workers = int(max_workers)

        upload_chunk = os.getenv("UPLOAD_CHUNK_SIZE")
        if upload_chunk is not None:
            self.uploads.DEFAULT_CHUNK_SIZE = int(upload_chunk)

        parallel_uploads = os.getenv("MAX_PARALLEL_UPLOADS")
        if parallel_uploads is not None:
            self.uploads.MAX_PARALLEL_UPLOADS = int(parallel_uploads)

        validator_rules = os.getenv("VALIDATOR_RULES")
        if validator_rules:
            try:
                import json

                rules = json.loads(validator_rules)
                if isinstance(rules, dict):
                    self.uploads.VALIDATOR_RULES.update(rules)
            except Exception:
                logging.getLogger(__name__).warning(
                    "Failed to parse VALIDATOR_RULES env var"
                )

        brokers = os.getenv("STREAMING_BROKERS")
        if brokers:
            self.streaming.brokers = brokers

        topic = os.getenv("STREAMING_TOPIC")
        if topic:
            self.streaming.topic = topic

        service_type = os.getenv("STREAMING_SERVICE")
        if service_type:
            self.streaming.service_type = service_type

        group = os.getenv("STREAMING_CONSUMER_GROUP")
        if group:
            self.streaming.consumer_group = group

        user = os.getenv("STREAMING_USERNAME")
        if user:
            self.streaming.username = user

        password = os.getenv("STREAMING_PASSWORD")
        if password:
            self.streaming.password = password

        for key, val in os.environ.items():
            match = re.match(r"RATE_LIMIT_(.+)_REQUESTS$", key)
            if not match:
                continue
            tier = match.group(1).lower()
            rl = self.security.rate_limits.setdefault(
                tier,
                RateLimitConfig(
                    self.security.rate_limit_requests,
                    self.security.rate_limit_window_minutes,
                    0,
                ),
            )
            try:
                rl.requests = int(val)
            except ValueError:
                logger.warning("Invalid requests limit for tier %s: %s", tier, val)
                continue
            if tier == "default":
                self.security.rate_limit_requests = rl.requests
            win_env = os.getenv(f"RATE_LIMIT_{tier.upper()}_WINDOW")
            if win_env is not None:
                rl.window_minutes = int(win_env)
                if tier == "default":
                    self.security.rate_limit_window_minutes = rl.window_minutes
            burst_env = os.getenv(f"RATE_LIMIT_{tier.upper()}_BURST")
            if burst_env is not None:
                rl.burst = int(burst_env)
        for tier, rl in self.security.rate_limits.items():
            prefix = f"RATE_LIMIT_{tier.upper()}_"
            if (req := os.getenv(f"{prefix}REQUESTS")) is not None:
                rl.requests = int(req)
                if tier == "default":
                    self.security.rate_limit_requests = rl.requests
            if (win := os.getenv(f"{prefix}WINDOW")) is not None:
                rl.window_minutes = int(win)
                if tier == "default":
                    self.security.rate_limit_window_minutes = rl.window_minutes
            if (burst := os.getenv(f"{prefix}BURST")) is not None:
                rl.burst = int(burst)

    def get_rate_limit(self, tier: str = "default") -> Dict[str, int]:
        rl = self.security.rate_limits.get(tier)
        if rl is None:
            rl = self.security.rate_limits.get(
                "default",
                RateLimitConfig(
                    self.security.rate_limit_requests,
                    self.security.rate_limit_window_minutes,
                    0,
                ),
            )
        return {
            "limit": rl.requests,
            "window": rl.window_minutes,
            "burst": rl.burst,
        }

    def get_security_level(self) -> int:
        return self.security.pbkdf2_iterations

    def get_max_upload_size(self) -> int:
        return self.get_max_upload_size_mb()

    def get_db_pool_size(self) -> int:
        return self.performance.db_pool_size

    def get_db_connection_timeout(self) -> int:
        return self.database.connection_timeout_seconds

    def get_css_thresholds(self) -> Dict[str, Any]:
        return {
            "bundle_threshold_kb": self.css.bundle_threshold_kb,
            "specificity_high": self.css.specificity_high,
        }

    def get_max_upload_size_bytes(self) -> int:
        """Get maximum upload size in bytes."""
        return self.get_max_upload_size_mb() * 1024 * 1024

    def validate_large_file_support(self) -> bool:
        """Check if configuration supports 50MB+ files."""
        return self.get_max_upload_size_mb() >= 50

    def get_max_parallel_uploads(self) -> int:
        return getattr(self.uploads, "MAX_PARALLEL_UPLOADS", 4)

    def get_validator_rules(self) -> Dict[str, Any]:
        return getattr(self.uploads, "VALIDATOR_RULES", {})


# Global instance
dynamic_config = DynamicConfigManager()


def diagnose_upload_config() -> None:
    """Diagnostic function to check upload configuration"""
    import os

    logger.info("=== Upload Configuration Diagnosis ===")
    logger.info("Environment MAX_UPLOAD_MB: %s", os.getenv("MAX_UPLOAD_MB", "Not Set"))
    logger.info("Dynamic Config max_upload_mb: %sMB", dynamic_config.security.max_upload_mb)
    logger.info("Upload folder: %s", dynamic_config.upload.folder)
    logger.info("Max file size: %sMB", dynamic_config.upload.max_file_size_mb)
    logger.info("Calculated max bytes: %s", f"{dynamic_config.get_max_upload_size_bytes():,}")
    logger.info("Supports 50MB+ files: %s", dynamic_config.validate_large_file_support())

    env_value = os.getenv("MAX_UPLOAD_MB")
    if env_value and int(env_value) < 50:
        logger.warning(
            "\u26a0\ufe0f  WARNING: Environment variable MAX_UPLOAD_MB=%s is too small!",
            env_value,
        )
        logger.info("   Run: unset MAX_UPLOAD_MB")


if __name__ == "__main__":
    diagnose_upload_config()
