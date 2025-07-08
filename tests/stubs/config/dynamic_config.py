class Security:
    max_upload_mb = 10

class Analytics:
    max_display_rows = 100
    chunk_size = 100
    max_memory_mb = 1024

class DynamicConfig:
    security = Security()
    analytics = Analytics()
    def get_max_upload_size_bytes(self):
        return 1024

dynamic_config = DynamicConfig()
