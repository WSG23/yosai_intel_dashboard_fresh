from dataclasses import dataclass

@dataclass
class SecurityConstants:
    """Security related default values with large file support"""
    pbkdf2_iterations: int = 100000
    salt_bytes: int = 32
    rate_limit_requests: int = 100
    rate_limit_window_minutes: int = 1
    max_upload_mb: int = 500  # Changed from 100 to 500
    max_file_size_mb: int = 500  # Added for consistency
    max_analysis_mb: int = 1000  # Added for large file processing

@dataclass
class PerformanceConstants:
    """Performance tuning defaults"""
    db_pool_size: int = 10
    ai_confidence_threshold: int = 75

@dataclass
class CSSConstants:
    """Thresholds for CSS quality metrics"""
    bundle_excellent_kb: int = 50
    bundle_good_kb: int = 100
    bundle_warning_kb: int = 200
    bundle_threshold_kb: int = 100
    specificity_high: int = 30
