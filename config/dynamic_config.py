import os
from typing import Dict, Any
from .constants import (
    SecurityConstants,
    PerformanceConstants,
    CSSConstants,
    AnalyticsConstants,
)

class DynamicConfigManager:
    """Loads constants and applies environment overrides."""

    def __init__(self) -> None:
        self.security = SecurityConstants()
        self.performance = PerformanceConstants()
        self.css = CSSConstants()
        self.analytics = AnalyticsConstants()
        self._load_yaml_config()
        self._apply_env_overrides()

    def _load_yaml_config(self) -> None:
        """Load configuration from YAML files."""
        import yaml
        from pathlib import Path

        try:
            config_env = os.getenv("YOSAI_ENV", "development")
            config_file = os.getenv("YOSAI_CONFIG_FILE")

            if config_file:
                config_path = Path(config_file)
            else:
                config_path = Path(f"config/{config_env}.yaml")
                if not config_path.exists():
                    config_path = Path("config/production.yaml")

            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)

                analytics_config = config_data.get("analytics", {})
                for key, value in analytics_config.items():
                    if hasattr(self.analytics, key):
                        setattr(self.analytics, key, value)

        except Exception:
            pass

    def _apply_env_overrides(self) -> None:
        """Override defaults from environment variables with validation."""
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
            value = int(max_upload)
            if value < 50:  # Prevent accidentally setting too small
                print(
                    f"WARNING: MAX_UPLOAD_MB={value} is too small for large files. Using 50MB minimum."
                )
                value = 50
            self.security.max_upload_mb = value
            self.security.max_file_size_mb = value  # Keep them in sync

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

        analytics_cache = os.getenv("ANALYTICS_CACHE_TIMEOUT")
        if analytics_cache is not None:
            self.analytics.cache_timeout_seconds = int(analytics_cache)

        chunk_size = os.getenv("ANALYTICS_CHUNK_SIZE")
        if chunk_size is not None:
            self.analytics.chunk_size = int(chunk_size)

        batch_size = os.getenv("ANALYTICS_BATCH_SIZE")
        if batch_size is not None:
            self.analytics.batch_size = int(batch_size)

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

    def get_max_upload_size_mb(self) -> int:
        """Get maximum upload size in MB."""
        return getattr(self.security, 'max_upload_mb', 100)

    def get_max_upload_size_bytes(self) -> int:
        """Get maximum upload size in bytes."""
        return self.get_max_upload_size_mb() * 1024 * 1024

    def validate_large_file_support(self) -> bool:
        """Check if configuration supports 50MB+ files."""
        return self.get_max_upload_size_mb() >= 50

# Global instance
dynamic_config = DynamicConfigManager()


def diagnose_upload_config():
    """Diagnostic function to check upload configuration"""
    from config.dynamic_config import dynamic_config
    import os

    print("=== Upload Configuration Diagnosis ===")
    print(f"Environment MAX_UPLOAD_MB: {os.getenv('MAX_UPLOAD_MB', 'Not Set')}")
    print(f"Dynamic Config max_upload_mb: {dynamic_config.security.max_upload_mb}MB")
    print(f"Calculated max bytes: {dynamic_config.get_max_upload_size_bytes():,}")
    print(f"Supports 50MB+ files: {dynamic_config.validate_large_file_support()}")

    if hasattr(dynamic_config.security, 'max_file_size_mb'):
        print(f"max_file_size_mb: {dynamic_config.security.max_file_size_mb}MB")

    # Check if environment is overriding to small value
    env_value = os.getenv('MAX_UPLOAD_MB')
    if env_value and int(env_value) < 50:
        print(f"\u26A0\uFE0F  WARNING: Environment variable MAX_UPLOAD_MB={env_value} is too small!")
        print("   Run: unset MAX_UPLOAD_MB")


if __name__ == "__main__":
    diagnose_upload_config()
