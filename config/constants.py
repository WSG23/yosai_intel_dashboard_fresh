"""Application-wide constants for Yōsai Intel Dashboard."""

from dataclasses import dataclass


class SecurityLimits:
    """Security-related validation limits."""

    MAX_INPUT_STRING_LENGTH_CHARACTERS: int = 50_000
    """Maximum characters allowed in user-provided strings.

    Range: 1_000-100_000. Higher values increase XSS risk; lower may truncate
    legitimate data.
    """


class DataProcessingLimits:
    """Data processing and memory management limits."""

    MAX_DATAFRAME_PROCESSING_ROWS_ROWS: int = 2_000_000
    """Maximum DataFrame rows processed in a single operation.

    Range: 100_000-5_000_000. Higher values risk memory exhaustion; lower
    reduces functionality.
    """


class FileProcessingLimits:
    """File upload and processing limits."""

    MAX_FILE_UPLOAD_SIZE_MB: int = 10
    """Default maximum file upload size for validation in megabytes.

    Range: 1-500. Higher values risk denial of service; lower may block
    legitimate uploads.
    """


@dataclass
class SecurityConstants:
    """Security related default values with large file support."""

    pbkdf2_iterations: int = 100000
    salt_bytes: int = 32
    rate_limit_requests: int = 100
    rate_limit_window_minutes: int = 1
    max_upload_mb: int = 500  # Changed from 100 to 500
    max_file_size_mb: int = 500  # Added for consistency
    max_analysis_mb: int = 1000  # Added for large file processing


@dataclass
class PerformanceConstants:
    """Performance tuning defaults."""

    db_pool_size: int = 10
    ai_confidence_threshold: int = 75


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
    enable_chunked_analysis: bool = True
    anomaly_detection_enabled: bool = True
    ml_models_path: str = "models/ml"
    data_retention_days: int = 30
    max_workers: int = 4
    query_timeout_seconds: int = 300

