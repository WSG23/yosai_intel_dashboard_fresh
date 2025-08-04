class Security:
    max_upload_mb = 10


from types import SimpleNamespace

from yosai_intel_dashboard.src.infrastructure.config.configuration_mixin import ConfigurationMixin


class Analytics:
    max_display_rows = 100
    chunk_size = 100
    max_memory_mb = 1024


class DynamicConfigManager(ConfigurationMixin):
    def __init__(self) -> None:
        self.security = SimpleNamespace(max_upload_mb=50)
        self.performance = SimpleNamespace(ai_confidence_threshold=75)
        self.uploads = SimpleNamespace(
            DEFAULT_CHUNK_SIZE=1,
            MAX_PARALLEL_UPLOADS=2,
            VALIDATOR_RULES={},
        )

    def get_max_upload_size_bytes(self):
        return self.get_max_upload_size_mb() * 1024 * 1024

    def validate_large_file_support(self):
        return self.get_max_upload_size_mb() >= 50

    def get_max_parallel_uploads(self):
        return self.uploads.MAX_PARALLEL_UPLOADS

    def get_validator_rules(self):
        return self.uploads.VALIDATOR_RULES

    def get_db_pool_size(self):
        return 10


# simple instance used in tests
dynamic_config = DynamicConfigManager()
