from __future__ import annotations

from datetime import datetime
from typing import Iterable, List, Optional, Tuple, Dict

import pandas as pd

from core.callback_controller import CallbackController, CallbackEvent
from core.unicode_processor import UnicodeProcessor


class UnsupportedFormatError(Exception):
    """Raised when no reader can parse a given file."""


class FormatDetector:
    """Try a series of readers to detect and load file formats."""

    def __init__(self, readers: Optional[Iterable] = None) -> None:
        self.readers: List = list(readers) if readers else []
        self.callback_controller = CallbackController()

    def detect_and_load(
        self, file_path: str, hint: Optional[Dict] = None
    ) -> Tuple[pd.DataFrame, Dict]:
        """Return ``DataFrame`` and metadata using the first succeeding reader."""
        hint = hint or {}
        for reader in self.readers:
            try:
                df = reader.read(file_path, hint=hint)
                df = UnicodeProcessor.sanitize_dataframe(df)
                meta = {
                    "source_path": file_path,
                    "ingest_ts": datetime.utcnow().isoformat(),
                    "detected_type": reader.format_name,
                    "original_columns": list(df.columns),
                    **hint,
                }
                return df, meta
            except reader.CannotParse as exc:
                self.callback_controller.fire_event(
                    CallbackEvent.SYSTEM_WARNING,
                    reader.format_name,
                    {"warning": str(exc)},
                )
                continue
        raise UnsupportedFormatError(file_path)

