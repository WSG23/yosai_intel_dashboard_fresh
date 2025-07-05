import logging
import time
from pathlib import Path
from typing import Callable, Optional, Sequence

from core.callback_manager import CallbackManager
from core.callback_events import CallbackEvent
from core.unicode import UnicodeProcessor
from services.data_processing.unified_file_validator import UnifiedFileValidator
from file_conversion.storage_manager import StorageManager

_logger = logging.getLogger(__name__)
callback_manager = CallbackManager()

# Simple in-memory metrics
_metrics = {
    "uploaded_files": 0,
    "migrated_files": 0,
    "total_rows": 0,
    "bytes_saved": 0,
    "total_time": 0.0,
}


def process_file_upload(
    contents: str,
    filename: str,
    *,
    storage: Optional[StorageManager] = None,
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
    storage = storage or StorageManager()
    validator = UnifiedFileValidator()
    start = time.perf_counter()

    df = validator.validate_file(contents, filename)
    df = UnicodeProcessor.sanitize_dataframe(df)

    base = Path(filename).stem
    ok, msg = storage.save_dataframe(df, base)
    if not ok:
        raise RuntimeError(msg)

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


def batch_migrate_legacy_files(
    paths: Sequence[str | Path] | Path,
    *,
    storage: Optional[StorageManager] = None,
    progress: Optional[Callable[[int, int, str], None]] = None,
) -> None:
    """Migrate pickled files to Parquet using :class:`StorageManager`.

    ``paths`` may be a directory or iterable of files. ``progress`` is called
    after each file with ``(index, total, filename)``.
    """
    storage = storage or StorageManager()
    if isinstance(paths, (str, Path)):
        pkl_files = sorted(Path(paths).glob("*.pkl"))
    else:
        pkl_files = [Path(p) for p in paths]

    total = len(pkl_files)
    for idx, pkl in enumerate(pkl_files, 1):
        success, _ = storage.migrate_pkl_to_parquet(pkl)
        if success:
            _metrics["migrated_files"] += 1
        if progress:
            try:
                progress(idx, total, pkl.name)
            except Exception as exc:  # pragma: no cover - best effort
                _logger.error("Progress callback failed: %s", exc)


def get_processing_metrics() -> dict:
    """Return a copy of internal processing metrics."""
    return dict(_metrics)


__all__ = [
    "process_file_upload",
    "batch_migrate_legacy_files",
    "get_processing_metrics",
]
