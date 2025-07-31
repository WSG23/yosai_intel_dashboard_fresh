"""Handle file uploads with validation and basic metrics."""

import logging
import time
from pathlib import Path
from typing import Callable, Optional, Sequence

from core.callback_events import CallbackEvent
from core.truly_unified_callbacks import TrulyUnifiedCallbacks
from core.unicode import UnicodeProcessor
from services.data_processing.file_handler import FileHandler
from utils.upload_store import UploadedDataStore

_logger = logging.getLogger(__name__)
callback_manager = TrulyUnifiedCallbacks()

# Simple in-memory metrics
_metrics = {
    "uploaded_files": 0,
    "total_rows": 0,
    "bytes_saved": 0,
    "total_time": 0.0,
}


def process_file_upload(
    contents: str,
    filename: str,
    *,
    storage: Optional[UploadedDataStore] = None,
) -> dict:
    """Validate ``contents``, sanitize with :class:`UnicodeProcessor` and save.

    Parameters
    ----------
    contents:
        Base64 encoded file contents.
    filename:
        Name of the uploaded file.
    storage:
        Optional :class:`StorageManager` instance.

    Returns
    -------
    dict
        Information about the processed file.
    """
    storage = storage or UploadedDataStore()
    validator = FileHandler()
    start = time.perf_counter()

    df = validator.validate_file(contents, filename)
    df = UnicodeProcessor.sanitize_dataframe(df)

    base = Path(filename).stem
    storage.add_file(base, df)

    callback_manager.trigger(
        CallbackEvent.DATA_PROCESSED,
        "unified_file_controller",
        {"filename": filename, "rows": len(df)},
    )

    _metrics["uploaded_files"] += 1
    _metrics["total_rows"] += len(df)
    _metrics["bytes_saved"] += df.memory_usage(deep=True).sum()
    _metrics["total_time"] += time.perf_counter() - start

    return {
        "rows": len(df),
        "columns": list(df.columns),
        "saved_as": f"{base}.parquet",
    }


def get_processing_metrics() -> dict:
    """Return a copy of internal processing metrics."""
    return dict(_metrics)


__all__ = [
    "process_file_upload",
    "get_processing_metrics",
]
