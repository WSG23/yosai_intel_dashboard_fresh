"""Helper to apply configuration overrides from environment variables."""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Mapping, Optional


class EnvironmentProcessor:
    """Apply environment settings to configuration objects."""

    log = logging.getLogger(__name__)

    def __init__(self, environ: Mapping[str, str] | None = None) -> None:
        self.env = environ if environ is not None else os.environ

    # ------------------------------------------------------------------
    def _to_int(self, name: str) -> Optional[int]:
        val = self.env.get(name)
        if val is None:
            return None
        try:
            return int(val)
        except ValueError:
            self.log.warning("Invalid %s value: %s", name, val)
            return None

    def _to_bool(self, name: str) -> Optional[bool]:
        val = self.env.get(name)
        if val is None:
            return None
        return val.lower() in {"1", "true", "yes"}

    def _load_json(self, name: str) -> Optional[dict[str, Any]]:
        val = self.env.get(name)
        if not val:
            return None
        try:
            data = json.loads(val)
            return data if isinstance(data, dict) else None
        except Exception:
            self.log.warning("Failed to parse %s env var", name)
            return None

    # ------------------------------------------------------------------
    def apply(self, config: Any) -> None:
        """Apply overrides to ``config`` in-place."""
        if hasattr(config, "app"):
            app = config.app
            if host := self.env.get("YOSAI_HOST"):
                app.host = host
            if (port := self._to_int("YOSAI_PORT")) is not None:
                app.port = port
            if (debug := self._to_bool("YOSAI_DEBUG")) is not None:
                app.debug = debug
            if secret := self.env.get("SECRET_KEY"):
                app.secret_key = secret

        if hasattr(config, "database"):
            db = config.database
            if url := self.env.get("DATABASE_URL"):
                db.url = url
            if name := self.env.get("DB_NAME"):
                db.name = name
            if host := self.env.get("DB_HOST"):
                db.host = host
            if (port := self._to_int("DB_PORT")) is not None:
                db.port = port
            if (timeout := self._to_int("DB_TIMEOUT")) is not None:
                db.connection_timeout = timeout
            if user := self.env.get("DB_USER"):
                db.user = user
            if pwd := self.env.get("DB_PASSWORD"):
                db.password = pwd

        if hasattr(config, "security"):
            sec = config.security
            if hasattr(sec, "pbkdf2_iterations"):
                if (v := self._to_int("PBKDF2_ITERATIONS")) is not None:
                    sec.pbkdf2_iterations = v
            if hasattr(sec, "rate_limit_requests"):
                if (v := self._to_int("RATE_LIMIT_API")) is not None:
                    sec.rate_limit_requests = v
            if hasattr(sec, "rate_limit_window_minutes"):
                if (v := self._to_int("RATE_LIMIT_WINDOW")) is not None:
                    sec.rate_limit_window_minutes = v
            if (val := self._to_int("MAX_UPLOAD_MB")) is not None:
                if val < 50 and hasattr(sec, "max_file_size_mb"):
                    print(
                        "WARNING: MAX_UPLOAD_MB="
                        f"{val} is too small. Using 50MB minimum."
                    )
                    val = 50
                sec.max_upload_mb = val
                if hasattr(sec, "max_file_size_mb"):
                    sec.max_file_size_mb = val
            if (val := self._to_int("MAX_UPLOAD_BYTES")) is not None:
                sec.max_upload_mb = val // (1024 * 1024)

        if hasattr(config, "performance"):
            perf = config.performance
            if (v := self._to_int("DB_POOL_SIZE")) is not None:
                perf.db_pool_size = v
            if (v := self._to_int("AI_CONFIDENCE_THRESHOLD")) is not None:
                perf.ai_confidence_threshold = v
            if (v := self._to_int("MEMORY_THRESHOLD_MB")) is not None:
                perf.memory_usage_threshold_mb = v

        if hasattr(config, "css"):
            css = config.css
            if (v := self._to_int("CSS_BUNDLE_THRESHOLD")) is not None:
                css.bundle_threshold_kb = v
            if (v := self._to_int("CSS_SPECIFICITY_HIGH")) is not None:
                css.specificity_high = v

        if hasattr(config, "analytics"):
            analytics = config.analytics
            if (v := self._to_int("ANALYTICS_CACHE_TIMEOUT")) is not None:
                analytics.cache_timeout_seconds = v
            if (v := self._to_int("ANALYTICS_CHUNK_SIZE")) is not None:
                analytics.chunk_size = v
            if (v := self._to_int("ANALYTICS_MIN_CHUNK_SIZE")) is not None:
                analytics.min_chunk_size = v
            if (v := self._to_int("ANALYTICS_BATCH_SIZE")) is not None:
                analytics.batch_size = v
            if (v := self._to_int("ANALYTICS_MAX_MEMORY_MB")) is not None:
                analytics.max_memory_mb = v
            if (v := self._to_int("ANALYTICS_MAX_WORKERS")) is not None:
                analytics.max_workers = v

        if hasattr(config, "uploads"):
            uploads = config.uploads
            if (v := self._to_int("UPLOAD_CHUNK_SIZE")) is not None:
                uploads.DEFAULT_CHUNK_SIZE = v
            if (v := self._to_int("MAX_PARALLEL_UPLOADS")) is not None:
                uploads.MAX_PARALLEL_UPLOADS = v
            if rules := self._load_json("VALIDATOR_RULES"):
                uploads.VALIDATOR_RULES.update(rules)


__all__ = ["EnvironmentProcessor"]
