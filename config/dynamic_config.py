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
        if os.getenv("PBKDF2_ITERATIONS"):
            self.security.pbkdf2_iterations = int(os.getenv("PBKDF2_ITERATIONS"))
        if os.getenv("RATE_LIMIT_API"):
            self.security.rate_limit_requests = int(os.getenv("RATE_LIMIT_API"))
        if os.getenv("RATE_LIMIT_WINDOW"):
            self.security.rate_limit_window_minutes = int(os.getenv("RATE_LIMIT_WINDOW"))
        if os.getenv("MAX_UPLOAD_MB"):
            self.security.max_upload_mb = int(os.getenv("MAX_UPLOAD_MB"))
        if os.getenv("DB_POOL_SIZE"):
            self.performance.db_pool_size = int(os.getenv("DB_POOL_SIZE"))
        if os.getenv("AI_CONFIDENCE_THRESHOLD"):
            self.performance.ai_confidence_threshold = int(os.getenv("AI_CONFIDENCE_THRESHOLD"))
        if os.getenv("CSS_BUNDLE_THRESHOLD"):
            self.css.bundle_threshold_kb = int(os.getenv("CSS_BUNDLE_THRESHOLD"))
        if os.getenv("CSS_SPECIFICITY_HIGH"):
            self.css.specificity_high = int(os.getenv("CSS_SPECIFICITY_HIGH"))

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
