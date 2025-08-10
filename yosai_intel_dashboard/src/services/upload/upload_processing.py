from __future__ import annotations

import hashlib
import mimetypes
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, BinaryIO, Dict

import pandas as pd

from unicode_toolkit import safe_encode_text
from yosai_intel_dashboard.src.utils.upload_store import get_uploaded_data_store

from ...core.protocols import EventBusProtocol
from ...infrastructure.callbacks.unified_callbacks import TrulyUnifiedCallbacks
from ...infrastructure.config.constants import (
    AnalyticsConstants,
    FileProcessingLimits,
)
from ..protocols.processor import ProcessorProtocol
from .protocols import UploadAnalyticsProtocol, UploadSecurityProtocol


@dataclass
class UploadResult:
    """Metadata returned after successfully streaming an upload."""

    filename: str
    bytes: int
    sha256: str
    content_type: str

    @property
    def contentType(self) -> str:  # pragma: no cover - alias for camelCase access
        return self.content_type


def stream_upload(
    source: BinaryIO,
    destination: str | Path,
    filename: str,
    *,
    max_bytes: int = FileProcessingLimits.MAX_FILE_UPLOAD_SIZE_MB * 1024 * 1024,
    allowed_extensions: set[str] | None = None,
    chunk_size: int = 1024 * 1024,
) -> UploadResult:
    """Stream ``source`` to ``destination`` enforcing limits and return metadata.

    The function writes the uploaded content to a temporary file while
    calculating its SHA-256 hash. Once streaming finishes successfully the
    temporary file is atomically moved to the final destination.
    """

    allowed = allowed_extensions or {".csv", ".json", ".xlsx"}

    dest_dir = Path(destination)
    dest_dir.mkdir(parents=True, exist_ok=True)

    safe_name = safe_encode_text(Path(filename).name).replace(" ", "_")
    ext = Path(safe_name).suffix.lower()
    if ext not in allowed:
        raise ValueError(f"Unsupported file extension: {ext}")

    hasher = hashlib.sha256()
    total = 0

    with tempfile.NamedTemporaryFile(dir=dest_dir, delete=False) as tmp:
        tmp_path = Path(tmp.name)
        while True:
            chunk = source.read(chunk_size)
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                tmp.close()
                try:
                    tmp_path.unlink()
                finally:
                    pass
                raise ValueError("file too large")
            hasher.update(chunk)
            tmp.write(chunk)

    final_path = dest_dir / safe_name
    os.replace(tmp_path, final_path)

    content_type = mimetypes.guess_type(safe_name)[0] or "application/octet-stream"

    return UploadResult(
        filename=safe_name,
        bytes=total,
        sha256=hasher.hexdigest(),
        content_type=content_type,
    )


class UploadAnalyticsProcessor(UploadAnalyticsProtocol):
    """Process and analyze uploaded access control data."""

    def __init__(
        self,
        validator: UploadSecurityProtocol,
        processor: ProcessorProtocol,
        callback_manager: TrulyUnifiedCallbacks,
        analytics_config: AnalyticsConstants,
        event_bus: EventBusProtocol,
    ) -> None:
        self.validator = validator
        self.processor = processor
        self.callback_manager = callback_manager
        self.analytics_config = analytics_config
        self.event_bus = event_bus

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------
    def get_analytics_from_uploaded_data(self) -> Dict[str, Any]:
        """Load uploaded data and return aggregated analytics."""
        try:
            data = self._load_data()
            if not data:
                return {"status": "no_data"}
            stats = self._process_uploaded_data_directly(data)
            return self._format_results(stats)
        except Exception as exc:  # pragma: no cover - best effort
            return {"status": "error", "message": str(exc)}

    def clean_uploaded_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Drop empty rows/columns and normalize column names in ``df``."""
        if df.empty:
            return df.copy()

        cleaned = df.dropna(how="all", axis=0).dropna(how="all", axis=1).copy()
        cleaned.columns = [c.strip().lower().replace(" ", "_") for c in cleaned.columns]
        cleaned = cleaned.rename(
            columns={"device_name": "door_id", "event_time": "timestamp"}
        )
        if "timestamp" in cleaned.columns:
            cleaned["timestamp"] = pd.to_datetime(cleaned["timestamp"], errors="coerce")
        cleaned = cleaned.dropna(how="all", axis=0)
        return cleaned

    def summarize_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Return basic statistics for ``df``."""

        total_events = len(df)
        active_users = df["person_id"].nunique() if "person_id" in df.columns else 0
        active_doors = df["door_id"].nunique() if "door_id" in df.columns else 0

        date_range = {"start": "Unknown", "end": "Unknown"}
        if "timestamp" in df.columns:
            ts = pd.to_datetime(df["timestamp"], errors="coerce").dropna()
            if not ts.empty:
                date_range = {
                    "start": str(ts.min().date()),
                    "end": str(ts.max().date()),
                }

        return {
            "rows": int(df.shape[0]),
            "columns": int(df.shape[1]),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "memory_usage": int(df.memory_usage(deep=True).sum()),
            "null_counts": {col: int(df[col].isna().sum()) for col in df.columns},
            "total_events": int(total_events),
            "active_users": int(active_users),
            "active_doors": int(active_doors),
            "date_range": date_range,
        }

    # ------------------------------------------------------------------
    # Internal helpers routed through public methods
    # ------------------------------------------------------------------
    def _load_data(self) -> Dict[str, pd.DataFrame]:
        """Return uploaded data using :meth:`load_uploaded_data`."""
        return self.load_uploaded_data()

    def _validate_data(self, data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """Clean uploaded dataframes and drop empty ones."""
        cleaned: Dict[str, pd.DataFrame] = {}
        for name, df in data.items():
            cleaned_df = self.clean_uploaded_dataframe(df)
            if not cleaned_df.empty:
                cleaned[name] = cleaned_df
        return cleaned

    def _calculate_statistics(self, data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Calculate statistics for validated ``data``."""
        if not data:
            return {
                "total_events": 0,
                "active_users": 0,
                "active_doors": 0,
                "date_range": {"start": "Unknown", "end": "Unknown"},
                "status": "no_data",
            }

        combined = pd.concat(list(data.values()), ignore_index=True)
        return self.summarize_dataframe(combined)

    def _format_results(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """Return final result dictionary with ``status`` key."""
        result = dict(stats)
        result["status"] = result.get("status", "success")
        return result

    # ------------------------------------------------------------------
    def _process_uploaded_data_directly(
        self, data: Dict[str, pd.DataFrame]
    ) -> Dict[str, Any]:
        """Backward compatible helper to process uploaded ``data``."""

        validated = self._validate_data(data)
        return self._calculate_statistics(validated)

    # ------------------------------------------------------------------
    def analyze_uploaded_data(self) -> Dict[str, Any]:
        """Public entry point for analysis of uploaded data."""
        return self.get_analytics_from_uploaded_data()

    def load_uploaded_data(self) -> Dict[str, pd.DataFrame]:
        """Retrieve all uploaded data from the shared store."""
        store = get_uploaded_data_store()
        return store.get_all_data()


# Expose commonly used methods at module level for convenience
get_analytics_from_uploaded_data = (
    UploadAnalyticsProcessor.get_analytics_from_uploaded_data
)
clean_uploaded_dataframe = UploadAnalyticsProcessor.clean_uploaded_dataframe
summarize_dataframe = UploadAnalyticsProcessor.summarize_dataframe

__all__ = [
    "UploadResult",
    "stream_upload",
    "UploadAnalyticsProcessor",
    "get_analytics_from_uploaded_data",
    "clean_uploaded_dataframe",
    "summarize_dataframe",
]
