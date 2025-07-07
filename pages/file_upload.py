from __future__ import annotations

"""File upload page wrapping the reusable upload component."""

import logging
from typing import Any, Dict, List

import pandas as pd

from components.file_upload_component import FileUploadComponent
from services.upload_data_service import (
    clear_uploaded_data as service_clear_uploaded_data,
)
from services.upload_data_service import get_file_info as service_get_file_info
from services.upload_data_service import get_uploaded_data as service_get_uploaded_data
from services.upload_data_service import (
    get_uploaded_filenames as service_get_uploaded_filenames,
)
from utils.upload_store import uploaded_data_store as _uploaded_data_store

logger = logging.getLogger(__name__)

_component = FileUploadComponent()


def layout():
    """Return the upload component layout."""
    return _component.layout()


def register_upload_callbacks(manager, controller=None) -> None:
    """Register callbacks for the upload component with ``manager.app``."""
    _component.register_callbacks(manager, controller)


def get_uploaded_data() -> Dict[str, pd.DataFrame]:
    """Get all uploaded data."""
    return service_get_uploaded_data()


def get_uploaded_filenames() -> List[str]:
    """Get list of uploaded filenames."""
    return service_get_uploaded_filenames()


def clear_uploaded_data() -> None:
    """Clear all uploaded data."""
    service_clear_uploaded_data()


def get_file_info() -> Dict[str, Dict[str, Any]]:
    """Return metadata about uploaded files."""
    return service_get_file_info()


def check_upload_system_health() -> Dict[str, Any]:
    """Perform simple checks on the upload subsystem."""
    issues: List[str] = []
    storage_dir = _uploaded_data_store.storage_dir
    try:
        tmp = storage_dir / "health.tmp"
        tmp.write_text("ok", encoding="utf-8")
        data = tmp.read_text(encoding="utf-8")
        if data != "ok":
            issues.append("Corrupt read after write")
        tmp.unlink()
    except Exception as exc:  # pragma: no cover - best effort
        issues.append(str(exc))
    return {"healthy": not issues, "issues": issues}


__all__ = [
    "layout",
    "register_upload_callbacks",
    "get_uploaded_data",
    "get_uploaded_filenames",
    "clear_uploaded_data",
    "get_file_info",
    "check_upload_system_health",
]
