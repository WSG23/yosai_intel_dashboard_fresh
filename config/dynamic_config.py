import logging
import os
from typing import Any, Dict, Protocol

from .constants import (
    AnalyticsConstants,
    CSSConstants,
    PerformanceConstants,
    SecurityConstants,
    UploadLimits,
)
from .app_config import UploadConfig
from .environment import select_config_file
from .env_overrides import apply_env_overrides


class ConfigurationServiceProtocol(Protocol):
    """Minimal configuration service interface."""

    def get_max_upload_size_mb(self) -> int:
        ...

    def get_max_upload_size_bytes(self) -> int:
        ...


class DynamicConfigManager:
    """Loads constants and applies environment overrides."""

    def __init__(self) -> None:
        self.security = SecurityConstants()
        self.performance = PerformanceConstants()
        self.css = CSSConstants()
        self.analytics = AnalyticsConstants()
        self.uploads = UploadLimits()
        self.upload = UploadConfig()
        self._load_yaml_config()
        self._apply_env_overrides()

    def _load_yaml_config(self) -> None:
        """Load configuration from YAML files."""
        import yaml

        try:
            config_path = select_config_file()

            if config_path and config_path.exists():

                class IncludeLoader(yaml.SafeLoader):
                    pass

                base_dir = config_path.parent

                def _include(loader: IncludeLoader, node: yaml.Node):
                    filename = loader.construct_scalar(node)
                    path = base_dir / filename
                    with open(path, "r") as inc:
                        return yaml.load(inc, Loader=IncludeLoader)

                IncludeLoader.add_constructor("!include", _include)

                with open(config_path, "r", encoding="utf-8") as f:
                    config_data = yaml.load(f, Loader=IncludeLoader)

                analytics_config = config_data.get("analytics", {})
                for key, value in analytics_config.items():
                    if hasattr(self.analytics, key):
                        setattr(self.analytics, key, value)

                uploads_config = config_data.get("uploads", {})
                for key, value in uploads_config.items():
                    if hasattr(self.uploads, key):
                        setattr(self.uploads, key, value)

        except Exception as exc:
            logging.getLogger(__name__).warning(
                "Failed to load %s: %s", config_path, exc
            )

    def _apply_env_overrides(self) -> None:
        """Override defaults from environment variables with validation."""
        apply_env_overrides(self)


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
        return getattr(self.upload, "max_file_size_mb", self.security.max_upload_mb)

    def get_max_upload_size_bytes(self) -> int:
        """Get maximum upload size in bytes."""
        return self.upload.max_file_size_bytes

    def validate_large_file_support(self) -> bool:
        """Check if configuration supports 50MB+ files."""
        return self.get_max_upload_size_mb() >= 50

    def get_upload_chunk_size(self) -> int:
        return getattr(self.uploads, "DEFAULT_CHUNK_SIZE", 50000)

    def get_max_parallel_uploads(self) -> int:
        return getattr(self.uploads, "MAX_PARALLEL_UPLOADS", 4)

    def get_validator_rules(self) -> Dict[str, Any]:
        return getattr(self.uploads, "VALIDATOR_RULES", {})


# Global instance
dynamic_config = DynamicConfigManager()


def diagnose_upload_config():
    """Diagnostic function to check upload configuration"""
    import os

    from config.dynamic_config import dynamic_config

    print("=== Upload Configuration Diagnosis ===")
    print(f"Environment MAX_UPLOAD_MB: {os.getenv('MAX_UPLOAD_MB', 'Not Set')}")
    print(f"Dynamic Config max_upload_mb: {dynamic_config.security.max_upload_mb}MB")
    print(f"Upload folder: {dynamic_config.upload.folder}")
    print(f"Max file size: {dynamic_config.upload.max_file_size_mb}MB")
    print(f"Calculated max bytes: {dynamic_config.get_max_upload_size_bytes():,}")
    print(f"Supports 50MB+ files: {dynamic_config.validate_large_file_support()}")

    # Check if environment is overriding to small value
    env_value = os.getenv("MAX_UPLOAD_MB")
    if env_value and int(env_value) < 50:
        print(
            "\u26a0\ufe0f  WARNING: Environment variable MAX_UPLOAD_MB="
            f"{env_value} is too small!"
        )
        print("   Run: unset MAX_UPLOAD_MB")


if __name__ == "__main__":
    diagnose_upload_config()
