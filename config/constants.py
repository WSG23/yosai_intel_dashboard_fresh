from dataclasses import dataclass

@dataclass
class SecurityConstants:
    """Security related default values"""
    pbkdf2_iterations: int = 100000
    salt_bytes: int = 32
    rate_limit_requests: int = 100
    rate_limit_window_minutes: int = 1
    max_upload_mb: int = 100

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
