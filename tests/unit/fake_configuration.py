from types import SimpleNamespace

from yosai_intel_dashboard.src.infrastructure.config.configuration_mixin import (
    ConfigurationMixin,
)


class FakeConfiguration(ConfigurationMixin):
    """Simple config for unit tests."""

    def __init__(self) -> None:
        self._database = {}
        self._app = SimpleNamespace(environment="development")
        self._security = SimpleNamespace(
            max_upload_mb=10,
            rate_limit_requests=100,
            rate_limit_window_minutes=1,
            pbkdf2_iterations=100000,
            salt_bytes=32,
        )
        self._analytics = SimpleNamespace(
            chunk_size=50000,
            max_display_rows=10000,
            max_memory_mb=1024,
        )
        self.uploads = SimpleNamespace(
            DEFAULT_CHUNK_SIZE=50000,
            MAX_PARALLEL_UPLOADS=4,
            VALIDATOR_RULES={},
        )
        self.performance = SimpleNamespace(
            memory_usage_threshold_mb=1024,
            ai_confidence_threshold=0.8,
        )
        self.css = SimpleNamespace(
            bundle_excellent_kb=50,
            bundle_good_kb=100,
            bundle_warning_kb=200,
            bundle_threshold_kb=100,
            specificity_high=30,
        )

    @property
    def analytics(self) -> SimpleNamespace:
        return self._analytics

    @property
    def database(self) -> dict:
        return self._database

    @property
    def security(self) -> SimpleNamespace:
        return self._security

    def get_database_config(self) -> dict:
        return self.database

    def get_app_config(self) -> dict:
        return self._app

    def get_security_config(self) -> dict:
        return vars(self.security)

    def get_upload_config(self) -> dict:
        return vars(self.uploads)

    def reload_config(self) -> None:
        pass

    def validate_config(self) -> dict:
        return {"valid": True}

    def get_max_upload_size_bytes(self) -> int:
        return self.get_max_upload_size_mb() * 1024 * 1024

    def validate_large_file_support(self) -> bool:
        return self.get_max_upload_size_mb() >= 50

    def get_max_parallel_uploads(self) -> int:
        from yosai_intel_dashboard.src.core.config import get_max_parallel_uploads

        return get_max_parallel_uploads()

    def get_validator_rules(self) -> dict:
        from yosai_intel_dashboard.src.core.config import get_validator_rules

        return get_validator_rules()

    def get_db_pool_size(self) -> int:
        return getattr(self.performance, "db_pool_size", 10)
