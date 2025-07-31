from __future__ import annotations

"""Simple configuration helpers used across the project."""

from typing import Any

from config.config import get_analytics_config
from config.dynamic_config import dynamic_config
from config.utils import get_ai_confidence_threshold as _get_ai_confidence_threshold
from config.utils import get_upload_chunk_size as _get_upload_chunk_size
from core.protocols import ConfigurationProtocol


def get_ai_confidence_threshold() -> float:
    """Return the AI confidence threshold from the dynamic configuration."""
    return _get_ai_confidence_threshold(dynamic_config)


def get_upload_chunk_size() -> int:
    """Return the upload chunk size from the dynamic configuration."""
    return _get_upload_chunk_size(dynamic_config)


def get_max_parallel_uploads() -> int:
    """Return the maximum number of parallel uploads from the dynamic configuration."""
    return dynamic_config.get_max_parallel_uploads()


def get_validator_rules() -> dict:
    """Return validator rules for uploads from the dynamic configuration."""
    return dynamic_config.get_validator_rules()


def get_max_upload_size_mb() -> int:
    """Return the maximum upload size in megabytes from the dynamic configuration."""
    return dynamic_config.get_max_upload_size_mb()


def get_max_upload_size_bytes() -> int:
    """Return the maximum upload size in bytes from the dynamic configuration."""
    return dynamic_config.get_max_upload_size_bytes()


def validate_large_file_support() -> bool:
    """Return ``True`` if large file uploads are supported."""
    return dynamic_config.validate_large_file_support()


def get_db_pool_size() -> int:
    """Return the configured database pool size."""
    return dynamic_config.get_db_pool_size()


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
