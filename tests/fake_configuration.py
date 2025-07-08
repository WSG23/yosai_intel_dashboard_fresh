from types import SimpleNamespace
from core.protocols import ConfigurationProtocol

class FakeConfiguration(ConfigurationProtocol):
    """Simple config for unit tests."""

    def __init__(self) -> None:
        self.database = {}
        self.app = {}
        self.security = SimpleNamespace(
            max_upload_mb=10,
            rate_limit_requests=100,
            rate_limit_window_minutes=1,
            pbkdf2_iterations=100000,
            salt_bytes=32,
        )
        self.analytics = SimpleNamespace(
            chunk_size=50000,
            max_display_rows=10000,
            max_memory_mb=1024,
        )
        self.uploads = SimpleNamespace(
            DEFAULT_CHUNK_SIZE=50000,
            MAX_PARALLEL_UPLOADS=4,
            VALIDATOR_RULES={},
        )
        self.performance = SimpleNamespace(memory_usage_threshold_mb=1024)
        self.css = SimpleNamespace(
            bundle_excellent_kb=50,
            bundle_good_kb=100,
            bundle_warning_kb=200,
            bundle_threshold_kb=100,
            specificity_high=30,
        )

    def get_database_config(self) -> dict:
        return self.database

    def get_app_config(self) -> dict:
        return self.app

    def get_security_config(self) -> dict:
        return vars(self.security)

    def get_upload_config(self) -> dict:
        return vars(self.uploads)

    def reload_config(self) -> None:
        pass

    def validate_config(self) -> dict:
        return {"valid": True}
