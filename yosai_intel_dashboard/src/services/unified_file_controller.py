"""Handle file uploads with validation and basic metrics."""

import logging
import time
from pathlib import Path
from typing import Callable, Optional, Sequence

from yosai_intel_dashboard.src.infrastructure.callbacks.events import CallbackEvent
from yosai_intel_dashboard.src.infrastructure.callbacks.unified_callbacks import TrulyUnifiedCallbacks
from yosai_intel_dashboard.src.core.unicode import UnicodeProcessor
from yosai_intel_dashboard.src.services.data_processing.file_handler import FileHandler
from yosai_intel_dashboard.src.utils.upload_store import UploadedDataStore

_logger = logging.getLogger(__name__)

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
    callback_manager: TrulyUnifiedCallbacks,
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


def register_callbacks(callbacks: TrulyUnifiedCallbacks) -> None:
    """Register event callbacks for file uploads using *callbacks* manager."""

    def _handle_upload(
        contents: str,
        filename: str,
        *,
        storage: Optional[UploadedDataStore] = None,
    ) -> dict:
        return process_file_upload(
            contents,
            filename,
            callback_manager=callbacks,
            storage=storage,
        )

    callbacks.register_event(CallbackEvent.FILE_UPLOAD_COMPLETE, _handle_upload)


__all__ = [
    "process_file_upload",
    "get_processing_metrics",
    "register_callbacks",
]
