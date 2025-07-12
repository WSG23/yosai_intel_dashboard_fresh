import json
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


def apply_env_overrides(config: Any) -> None:
    """Apply environment variable overrides to ``config``.

    The function supports both :class:`~config.base.Config` objects and the
    :class:`~config.dynamic_config.DynamicConfigManager` used for constants.
    Only attributes present on the passed object will be modified.
    """

    # --- App overrides -------------------------------------------------
    if hasattr(config, "app"):
        app = config.app
        if host := os.getenv("YOSAI_HOST"):
            app.host = host
        if port := os.getenv("YOSAI_PORT"):
            try:
                app.port = int(port)
            except ValueError:
                logger.warning("Invalid YOSAI_PORT value: %s", port)
        if debug := os.getenv("YOSAI_DEBUG"):
            app.debug = debug.lower() in ("true", "1", "yes")
        if secret := os.getenv("SECRET_KEY"):
            app.secret_key = secret

    # --- Database overrides --------------------------------------------
    if hasattr(config, "database"):
        db = config.database
        if db_url := os.getenv("DATABASE_URL"):
            db.url = db_url
        if db_name := os.getenv("DB_NAME"):
            db.name = db_name
        if db_host := os.getenv("DB_HOST"):
            db.host = db_host
        if db_port := os.getenv("DB_PORT"):
            try:
                db.port = int(db_port)
            except ValueError:
                logger.warning("Invalid DB_PORT value: %s", db_port)
        if db_timeout := os.getenv("DB_TIMEOUT"):
            try:
                db.connection_timeout = int(db_timeout)
            except ValueError:
                logger.warning("Invalid DB_TIMEOUT value: %s", db_timeout)
        if db_user := os.getenv("DB_USER"):
            db.user = db_user
        if db_pass := os.getenv("DB_PASSWORD"):
            db.password = db_pass

    # --- Security overrides -------------------------------------------
    if hasattr(config, "security"):
        sec = config.security
        if hasattr(sec, "pbkdf2_iterations") and (
            val := os.getenv("PBKDF2_ITERATIONS")
        ):
            sec.pbkdf2_iterations = int(val)
        if hasattr(sec, "rate_limit_requests") and (val := os.getenv("RATE_LIMIT_API")):
            sec.rate_limit_requests = int(val)
        if hasattr(sec, "rate_limit_window_minutes") and (
            val := os.getenv("RATE_LIMIT_WINDOW")
        ):
            sec.rate_limit_window_minutes = int(val)
        if (max_upload := os.getenv("MAX_UPLOAD_MB")) is not None:
            try:
                value = int(max_upload)
            except ValueError:
                logger.warning("Invalid MAX_UPLOAD_MB value: %s", max_upload)
            else:
                if value < 50 and hasattr(sec, "max_file_size_mb"):
                    print(
                        "WARNING: MAX_UPLOAD_MB="
                        f"{value} is too small. Using 50MB minimum."
                    )
                    value = 50
                sec.max_upload_mb = value
                if hasattr(sec, "max_file_size_mb"):
                    sec.max_file_size_mb = value
        if (max_upload_bytes := os.getenv("MAX_UPLOAD_BYTES")) is not None:
            try:
                sec.max_upload_mb = int(max_upload_bytes) // (1024 * 1024)
            except ValueError:
                logger.warning("Invalid MAX_UPLOAD_BYTES value: %s", max_upload_bytes)

    # --- Performance overrides ----------------------------------------
    if hasattr(config, "performance"):
        perf = config.performance
        if db_pool := os.getenv("DB_POOL_SIZE"):
            perf.db_pool_size = int(db_pool)
        if ai_thresh := os.getenv("AI_CONFIDENCE_THRESHOLD"):
            perf.ai_confidence_threshold = int(ai_thresh)
        if mem_thresh := os.getenv("MEMORY_THRESHOLD_MB"):
            perf.memory_usage_threshold_mb = int(mem_thresh)

    # --- CSS overrides -------------------------------------------------
    if hasattr(config, "css"):
        css = config.css
        if val := os.getenv("CSS_BUNDLE_THRESHOLD"):
            css.bundle_threshold_kb = int(val)
        if val := os.getenv("CSS_SPECIFICITY_HIGH"):
            css.specificity_high = int(val)

    # --- Analytics overrides -----------------------------------------
    if hasattr(config, "analytics"):
        analytics = config.analytics
        if val := os.getenv("ANALYTICS_CACHE_TIMEOUT"):
            analytics.cache_timeout_seconds = int(val)
        if val := os.getenv("ANALYTICS_CHUNK_SIZE"):
            analytics.chunk_size = int(val)
        if val := os.getenv("ANALYTICS_MIN_CHUNK_SIZE"):
            analytics.min_chunk_size = int(val)
        if val := os.getenv("ANALYTICS_BATCH_SIZE"):
            analytics.batch_size = int(val)
        if val := os.getenv("ANALYTICS_MAX_MEMORY_MB"):
            analytics.max_memory_mb = int(val)
        if val := os.getenv("ANALYTICS_MAX_WORKERS"):
            analytics.max_workers = int(val)

    # --- Uploads overrides -------------------------------------------
    if hasattr(config, "uploads"):
        uploads = config.uploads
        if val := os.getenv("UPLOAD_CHUNK_SIZE"):
            uploads.DEFAULT_CHUNK_SIZE = int(val)
        if val := os.getenv("MAX_PARALLEL_UPLOADS"):
            uploads.MAX_PARALLEL_UPLOADS = int(val)
        if rules := os.getenv("VALIDATOR_RULES"):
            try:
                parsed = json.loads(rules)
                if isinstance(parsed, dict):
                    uploads.VALIDATOR_RULES.update(parsed)
            except Exception:
                logger.warning("Failed to parse VALIDATOR_RULES env var")


__all__ = ["apply_env_overrides"]
