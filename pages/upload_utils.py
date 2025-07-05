"""Utility helpers for uploaded data access."""

import logging
from typing import Any, Dict, List

import pandas as pd

from utils.upload_store import uploaded_data_store as _uploaded_data_store
from services.upload_data_service import (
    get_uploaded_data as service_get_uploaded_data,
    get_uploaded_filenames as service_get_uploaded_filenames,
    clear_uploaded_data as service_clear_uploaded_data,
    get_file_info as service_get_file_info,
)

logger = logging.getLogger(__name__)


def get_uploaded_data() -> Dict[str, pd.DataFrame]:
    """Get all uploaded data (for use by analytics)."""
    return service_get_uploaded_data()


def get_uploaded_filenames() -> List[str]:
    """Get list of uploaded filenames."""
    return service_get_uploaded_filenames()


def clear_uploaded_data() -> None:
    """Clear all uploaded data."""
    service_clear_uploaded_data()


def get_file_info() -> Dict[str, Dict[str, Any]]:
    """Get information about uploaded files."""
    return service_get_file_info()


def check_upload_system_health() -> Dict[str, Any]:
    """Monitor upload system health."""
    issues = []
    storage_dir = _uploaded_data_store.storage_dir

    if not storage_dir.exists():
        issues.append(f"Storage directory missing: {storage_dir}")

    try:
        test_file = storage_dir / "test.tmp"
        test_file.write_text("test")
        test_file.unlink()
    except Exception as e:  # noqa: BLE001
        issues.append(f"Cannot write to storage directory: {e}")

    pending = len(_uploaded_data_store._save_futures)
    if pending > 10:
        issues.append(f"Too many pending saves: {pending}")

    return {"healthy": len(issues) == 0, "issues": issues}


__all__ = [
    "_uploaded_data_store",
    "get_uploaded_data",
    "get_uploaded_filenames",
    "clear_uploaded_data",
    "get_file_info",
    "check_upload_system_health",
]

