"""Application-wide constants for Yōsai Intel Dashboard."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict

# Default chunk size used across services when reading or uploading large files
DEFAULT_CHUNK_SIZE: int = 50_000
# Default chunk size for database migration utilities
MIGRATION_CHUNK_SIZE: int = 1_000
# File extensions supported across upload services
UPLOAD_ALLOWED_EXTENSIONS = {".csv", ".json", ".xlsx", ".xls"}


class SecurityLimits:
    """Security-related validation limits."""

    MAX_INPUT_STRING_LENGTH_CHARACTERS: int = 50_000
    """Maximum characters allowed in user-provided strings.

    Range: 1_000-100_000. Higher values increase XSS risk; lower may truncate
    legitimate data.
    """


class DataProcessingLimits:
    """Data processing and memory management limits."""

    MAX_DATAFRAME_PROCESSING_ROWS: int = 2_000_000
    """Maximum DataFrame rows processed in a single operation.

    Range: 100_000-5_000_000. Higher values risk memory exhaustion; lower
    reduces functionality.
    """

    CHUNKING_ROW_THRESHOLD: int = 500_000
    """Row count above which chunked analysis is triggered."""

    SMALL_DATASET_ROW_THRESHOLD: int = 100_000
    """Upper row count limit considered a small dataset."""

    MIN_CHUNK_SIZE: int = 5_000
    MAX_CHUNK_SIZE: int = 100_000
    SMALL_DATA_CHUNK_ROWS: int = 10_000
    DEFAULT_QUERY_LIMIT: int = 10_000


class UploadLimits:
    """Defaults for chunked uploads and validation."""

    DEFAULT_CHUNK_SIZE: int = 50_000
    MAX_PARALLEL_UPLOADS: int = 4
    VALIDATOR_RULES: dict = {
        "sql_injection": True,
        "xss": True,
        "path_traversal": True,
    }


class FileProcessingLimits:
    """File upload and processing limits."""

    MAX_FILE_UPLOAD_SIZE_MB: int = 10
    """Default maximum file upload size for validation in megabytes.

    Range: 1-500. Higher values risk denial of service; lower may block
    legitimate uploads.
    """

    LARGE_FILE_THRESHOLD_MB: int = 50
    """File size threshold considered large in megabytes."""

    CSV_SAMPLE_SIZE_SMALL: int = 8192
    """Default sample size for delimiter detection in bytes."""

    CSV_SAMPLE_SIZE_LARGE: int = 65536
    """Larger sample size for big files in bytes."""


@dataclass
class RateLimitConfig:
    """Configuration for a single API tier rate limit."""

    requests: int
    window_minutes: int
    burst: int = 0


@dataclass
class SecurityConstants:
    """Security related default values with large file support."""

    pbkdf2_iterations: int = 100000
    salt_bytes: int = 32
    rate_limit_requests: int = 200
    rate_limit_window_minutes: int = 1
    rate_limits: Dict[str, RateLimitConfig] = field(
        default_factory=lambda: {"default": RateLimitConfig(200, 1, 0)}
    )
    max_upload_mb: int = 500  # Changed from 100 to 500
    max_file_size_mb: int = 500  # Added for consistency
    max_analysis_mb: int = 1000  # Added for large file processing


@dataclass
class PerformanceConstants:
    """Performance tuning defaults."""

    db_pool_size: int = 10
    ai_confidence_threshold: int = 75
    memory_usage_threshold_mb: int = 1024
    profiling_enabled: bool = False


@dataclass
class DatabaseConstants:
    """Database related defaults."""

    connection_timeout_seconds: int = 30
    async_pool_min_size: int = 1
    async_pool_max_size: int = 10
    async_connection_timeout_seconds: int = 30


@dataclass
class StreamingConstants:
    """Defaults for streaming configuration."""

    service_type: str = "kafka"
    brokers: str = "localhost:9092"
    topic: str = "events"
    consumer_group: str = "yosai"
    username: str = ""
    password: str = ""


@dataclass
class CSSConstants:
    """Thresholds for CSS quality metrics."""

    bundle_excellent_kb: int = 50
    bundle_good_kb: int = 100
    bundle_warning_kb: int = 200
    bundle_threshold_kb: int = 100
    specificity_high: int = 30


@dataclass
class AnalyticsConstants:
    """Analytics processing defaults for large datasets."""

    cache_timeout_seconds: int = 60
    max_records_per_query: int = 500000
    enable_real_time: bool = True
    batch_size: int = 25000
    chunk_size: int = 50000
    min_chunk_size: int = 10000
    enable_chunked_analysis: bool = True
    anomaly_detection_enabled: bool = True
    ml_models_path: str = "models/ml"
    data_retention_days: int = 30
    max_workers: int = 4
    query_timeout_seconds: int = 300
    max_memory_mb: int = 1024
    max_display_rows: int = 10000
    row_limit_warning: int = 150
    large_data_threshold: int = 1000


@dataclass
class AnalysisThresholds:
    """Threshold values used in analytics calculations."""

    failed_attempt_threshold: int = 3
    high_failure_severity: int = 5
    rapid_attempt_seconds: int = 30
    rapid_attempt_threshold: int = 2


@dataclass
class CacheConstants:
    """Settings for analytics result caching."""

    max_items: int = 100
    purge_count: int = 50


# Convenience constant for data previews
MAX_DISPLAY_ROWS: int = AnalyticsConstants.max_display_rows


# Network defaults
DEFAULT_APP_HOST: str = "127.0.0.1"
DEFAULT_APP_PORT: int = 8050

# Default port for the Flask API
DEFAULT_API_PORT: int = 5001
API_PORT: int = int(os.getenv("API_PORT", DEFAULT_API_PORT))

DEFAULT_DB_HOST: str = "localhost"
DEFAULT_DB_PORT: int = 5432

DEFAULT_CACHE_HOST: str = "localhost"
DEFAULT_CACHE_PORT: int = 6379
