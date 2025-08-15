"""Handle file uploads with validation and basic metrics."""

import asyncio
import base64
import io
import logging
import mimetypes
import time
from pathlib import Path
from typing import Callable, Optional, Sequence

from yosai_intel_dashboard.src.core.unicode import UnicodeProcessor
from yosai_intel_dashboard.src.infrastructure.callbacks.events import CallbackEvent
from yosai_intel_dashboard.src.infrastructure.callbacks.unified_callbacks import TrulyUnifiedCallbacks
from yosai_intel_dashboard.src.infrastructure.config.dynamic_config import dynamic_config
from yosai_intel_dashboard.src.services.data_processing.file_handler import FileHandler
from yosai_intel_dashboard.src.utils.sanitization import sanitize_text
from yosai_intel_dashboard.src.utils.upload_store import UploadedDataStore

_logger = logging.getLogger(__name__)

# Simple in-memory metrics
_metrics = {
    "uploaded_files": 0,
    "total_rows": 0,
    "bytes_saved": 0,
    "total_time": 0.0,
}

ALLOWED_EXTENSIONS = {".csv", ".json", ".xlsx", ".xls"}
ALLOWED_MIME_TYPES = {
    "text/csv",
    "application/json",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


def _scan_for_malware(data: bytes) -> None:
    """Scan *data* using clamd if available.

    Raises a ``ValueError`` if malware is detected. If the scanner is not
    available the function returns silently.
    """

    try:  # pragma: no cover - optional dependency
        import clamd

        cd = clamd.ClamdUnixSocket()
        result = cd.instream(io.BytesIO(data))
        if isinstance(result, dict):
            status = result.get("stream", {}).get("status")
            if status == "FOUND":
                raise ValueError("Virus detected")
    except Exception:
        # Fail open if clamd is not available
        return


async def process_file_upload(
    contents: str,
    filename: str,
    *,
    callback_manager: TrulyUnifiedCallbacks,
    storage: Optional[UploadedDataStore] = None,
) -> dict:
    """Validate ``contents``, sanitize with :class:`UnicodeProcessor` and save.

    This asynchronous variant offloads blocking operations like file validation
    and disk writes to worker threads.  Event callbacks are dispatched using the
    async interface and executed in parallel with storage operations.

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

    filename = sanitize_text(filename)
    try:
        header, data = contents.split(",", 1)
    except ValueError:
        raise ValueError("Invalid file contents")
    file_bytes = base64.b64decode(data)
    max_bytes = dynamic_config.security.max_upload_mb * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise ValueError("File too large")
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError("Invalid file extension")
    mime = mimetypes.guess_type(filename)[0] or ""
    if mime not in ALLOWED_MIME_TYPES:
        raise ValueError("Invalid MIME type")

    # Scan for malware and validate file contents concurrently since both may
    # involve I/O or heavy processing.
    scan_task = asyncio.to_thread(_scan_for_malware, file_bytes)
    validate_task = asyncio.to_thread(validator.validate_file, contents, filename)
    _, df = await asyncio.gather(scan_task, validate_task)
    df = UnicodeProcessor.sanitize_dataframe(df)

    base = Path(filename).stem
    # Persist file and publish event concurrently.
    add_file = asyncio.to_thread(storage.add_file, base, df)
    dispatch = callback_manager.trigger_async(
        CallbackEvent.DATA_PROCESSED,
        "unified_file_controller",
        {"filename": filename, "rows": len(df)},
    )
    await asyncio.gather(add_file, dispatch)

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

    async def _handle_upload(
        contents: str,
        filename: str,
        *,
        storage: Optional[UploadedDataStore] = None,
    ) -> dict:
        return await process_file_upload(
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
