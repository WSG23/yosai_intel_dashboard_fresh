from __future__ import annotations

"""Simple configuration helpers used across the project."""

from typing import Any

from core.protocols import ConfigurationProtocol
from yosai_intel_dashboard.src.infrastructure.config.config import get_analytics_config
from yosai_intel_dashboard.src.infrastructure.config.constants import (
    DEFAULT_CHUNK_SIZE,
    FileProcessingLimits,
    UploadLimits,
)
from config.dynamic_config import (
    dynamic_config,
)


def get_ai_confidence_threshold() -> float:
    """Default confidence threshold for AI based features."""
    return 0.85


def get_upload_chunk_size() -> int:
    """Default chunk size for uploads."""
    return DEFAULT_CHUNK_SIZE


def get_max_parallel_uploads() -> int:
    """Number of parallel uploads allowed."""
    return UploadLimits.MAX_PARALLEL_UPLOADS


def get_validator_rules() -> dict:
    """Return validator rules for uploads."""
    return UploadLimits.VALIDATOR_RULES


def get_max_upload_size_mb() -> int:
    """Maximum upload size allowed in megabytes."""
    return FileProcessingLimits.MAX_FILE_UPLOAD_SIZE_MB


def get_max_upload_size_bytes() -> int:
    """Maximum upload size allowed in bytes."""
    return get_max_upload_size_mb() * 1024 * 1024


def validate_large_file_support() -> bool:
    """Whether large file uploads are supported."""
    return get_max_upload_size_mb() >= 50


def get_db_pool_size() -> int:
    """Default database connection pool size."""
    return 10


def get_max_display_rows(config: ConfigurationProtocol = dynamic_config) -> int:
    """Return maximum number of rows to show in previews."""
    try:
        return (
            get_analytics_config().max_display_rows or config.analytics.max_display_rows
        )
    except Exception:
        return config.analytics.max_display_rows


__all__ = [
    "get_ai_confidence_threshold",
    "get_upload_chunk_size",
    "get_max_parallel_uploads",
    "get_validator_rules",
    "get_max_upload_size_mb",
    "get_max_upload_size_bytes",
    "validate_large_file_support",
    "get_db_pool_size",
    "get_max_display_rows",
]
