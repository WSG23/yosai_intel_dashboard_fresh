class Security:
    max_upload_mb = 10


class Analytics:
    max_display_rows = 100
    chunk_size = 100
    max_memory_mb = 1024


from yosai_intel_dashboard.src.infrastructure.config.utils import get_ai_confidence_threshold, get_upload_chunk_size
from core.config import get_max_parallel_uploads, get_validator_rules


class DynamicConfigManager:
    def get_max_upload_size_mb(self):
        return Security.max_upload_mb

    def get_max_upload_size_bytes(self):
        return Security.max_upload_mb * 1024 * 1024

    def validate_large_file_support(self):
        return True

    def get_upload_chunk_size(self):
        return get_upload_chunk_size()

    def get_max_parallel_uploads(self):
        return get_max_parallel_uploads()

    def get_validator_rules(self):
        return get_validator_rules()

    def get_ai_confidence_threshold(self):
        return get_ai_confidence_threshold()

    def get_db_pool_size(self):
        return 10


# simple instance used in tests
dynamic_config = DynamicConfigManager()
