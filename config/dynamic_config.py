import os
from typing import Dict, Any
from .constants import SecurityConstants, PerformanceConstants, CSSConstants

class DynamicConfigManager:
    """Loads constants and applies environment overrides."""

    def __init__(self) -> None:
        self.security = SecurityConstants()
        self.performance = PerformanceConstants()
        self.css = CSSConstants()
        self._apply_env_overrides()

    def _apply_env_overrides(self) -> None:
        """Override defaults from environment variables."""
        iterations = os.getenv("PBKDF2_ITERATIONS")
        if iterations is not None:
            self.security.pbkdf2_iterations = int(iterations)

        rate_limit_api = os.getenv("RATE_LIMIT_API")
        if rate_limit_api is not None:
            self.security.rate_limit_requests = int(rate_limit_api)

        rate_limit_window = os.getenv("RATE_LIMIT_WINDOW")
        if rate_limit_window is not None:
            self.security.rate_limit_window_minutes = int(rate_limit_window)

        max_upload = os.getenv("MAX_UPLOAD_MB")
        if max_upload is not None:
            self.security.max_upload_mb = int(max_upload)

        db_pool = os.getenv("DB_POOL_SIZE")
        if db_pool is not None:
            self.performance.db_pool_size = int(db_pool)

        ai_threshold = os.getenv("AI_CONFIDENCE_THRESHOLD")
        if ai_threshold is not None:
            self.performance.ai_confidence_threshold = int(ai_threshold)

        css_threshold = os.getenv("CSS_BUNDLE_THRESHOLD")
        if css_threshold is not None:
            self.css.bundle_threshold_kb = int(css_threshold)

        css_specificity = os.getenv("CSS_SPECIFICITY_HIGH")
        if css_specificity is not None:
            self.css.specificity_high = int(css_specificity)

    def get_rate_limit(self) -> Dict[str, int]:
        return {
            "requests": self.security.rate_limit_requests,
            "window_minutes": self.security.rate_limit_window_minutes,
        }

    def get_security_level(self) -> int:
        return self.security.pbkdf2_iterations

    def get_max_upload_size(self) -> int:
        return self.security.max_upload_mb

    def get_db_pool_size(self) -> int:
        return self.performance.db_pool_size

    def get_css_thresholds(self) -> Dict[str, Any]:
        return {
            "bundle_threshold_kb": self.css.bundle_threshold_kb,
            "specificity_high": self.css.specificity_high,
        }

    def get_ai_confidence_threshold(self) -> int:
        return self.performance.ai_confidence_threshold

# Global instance
dynamic_config = DynamicConfigManager()
