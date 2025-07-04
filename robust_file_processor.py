"""Simple robust file processor with Unicode handling."""

from __future__ import annotations

import io
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import pandas as pd

from unicode_handler import UnicodeProcessor
from callback_controller import CallbackController, CallbackEvent

logger = logging.getLogger(__name__)


class FileProcessingError(Exception):
    """Raised when file processing fails."""


class RobustFileProcessor:
    """Process common file types with basic Unicode handling."""

    def __init__(self, controller: Optional[CallbackController] = None) -> None:
        self.controller = controller or CallbackController()

    def process_file(
        self,
        content: bytes,
        filename: str,
        source_id: str | None = None,
    ) -> Tuple[pd.DataFrame, Optional[str]]:
        """Process file and return ``(DataFrame, error)``."""
        source = source_id or "processor"
        self.controller.fire_event(
            CallbackEvent.FILE_PROCESSING_START,
            source,
            {"filename": filename},
        )

        if not content:
            error = "File is empty"
            self.controller.fire_event(
                CallbackEvent.FILE_PROCESSING_ERROR, source, {"error": error}
            )
            return pd.DataFrame(), error

        ext = Path(filename).suffix.lower()
        try:
            if ext == ".csv":
                text = UnicodeProcessor.safe_decode_bytes(content)
                df = pd.read_csv(io.StringIO(text))
            elif ext == ".json":
                text = UnicodeProcessor.safe_decode_bytes(content)
                obj = json.loads(text)
                df = pd.DataFrame(obj if isinstance(obj, list) else [obj])
            elif ext in {".xlsx", ".xls"}:
                df = pd.read_excel(io.BytesIO(content))
            else:
                raise FileProcessingError(f"Unsupported file type: {ext}")
            df = UnicodeProcessor.sanitize_dataframe(df)
            error = None
        except Exception as exc:  # pragma: no cover - best effort
            df = pd.DataFrame()
            error = str(exc)

        if error is None:
            self.controller.fire_event(
                CallbackEvent.FILE_PROCESSING_COMPLETE,
                source,
                {"rows": len(df), "columns": len(df.columns)},
            )
        else:
            self.controller.fire_event(
                CallbackEvent.FILE_PROCESSING_ERROR, source, {"error": error}
            )
        return df, error

    @staticmethod
    def validate_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
        """Return simple validation metrics for ``df``."""
        empty_ratio = float(df.isna().mean().mean()) if not df.empty else 0.0
        return {
            "valid": True,
            "rows": len(df),
            "columns": len(df.columns),
            "empty_ratio": empty_ratio,
            "column_names": list(df.columns),
        }

def process_file_simple(
    content: bytes,
    filename: str,
    source_id: str | None = None,
) -> Tuple[pd.DataFrame, Optional[str]]:
    """Convenience wrapper around :class:`RobustFileProcessor`."""

    processor = RobustFileProcessor()
    return processor.process_file(content, filename, source_id)


__all__ = [
    "RobustFileProcessor",
    "process_file_simple",
    "FileProcessingError",
]
