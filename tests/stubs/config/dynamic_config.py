class Security:
    max_upload_mb = 10


class Analytics:
    max_display_rows = 100
    chunk_size = 100
    max_memory_mb = 1024


class DynamicConfigManager:
    def get_max_upload_size_mb(self):
        return Security.max_upload_mb

    def get_max_upload_size_bytes(self):
        return Security.max_upload_mb * 1024 * 1024

    def validate_large_file_support(self):
        return True

    def get_upload_chunk_size(self):
        return Analytics.chunk_size

    def get_max_parallel_uploads(self):
        return 1

    def get_validator_rules(self):
        return {}

    def get_ai_confidence_threshold(self):
        return 80

    def get_db_pool_size(self):
        return 10


# simple instance used in tests
dynamic_config = DynamicConfigManager()
