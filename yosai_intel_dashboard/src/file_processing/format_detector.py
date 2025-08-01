from __future__ import annotations

from datetime import datetime
from typing import Dict, Iterable, List, Optional, Tuple

import pandas as pd

from yosai_intel_dashboard.src.infrastructure.callbacks.events import CallbackEvent
from yosai_intel_dashboard.src.infrastructure.callbacks.unified_callbacks import TrulyUnifiedCallbacks
from yosai_intel_dashboard.src.core.container import get_unicode_processor
from yosai_intel_dashboard.src.core.interfaces.protocols import UnicodeProcessorProtocol
from yosai_intel_dashboard.src.infrastructure.callbacks.unified_callbacks import TrulyUnifiedCallbacks


class UnsupportedFormatError(Exception):
    """Raised when no reader can parse a given file."""


class FormatDetector:
    """Try a series of readers to detect and load file formats."""

    def __init__(
        self,
        readers: Optional[Iterable] = None,
        *,
        unicode_processor: UnicodeProcessorProtocol | None = None,
    ) -> None:
        self.readers: List = list(readers) if readers else []
        self.unified_callbacks = TrulyUnifiedCallbacks()
        self.unicode_processor = unicode_processor or get_unicode_processor()

    def detect_and_load(
        self, file_path: str, hint: Optional[Dict] = None
    ) -> Tuple[pd.DataFrame, Dict]:
        """Return ``DataFrame`` and metadata using the first succeeding reader."""
        hint = hint or {}
        for reader in self.readers:
            try:
                df = reader.read(file_path, hint=hint)
                df = self.unicode_processor.sanitize_dataframe(df)
                meta = {
                    "source_path": file_path,
                    "ingest_ts": datetime.utcnow().isoformat(),
                    "detected_type": reader.format_name,
                    "original_columns": list(df.columns),
                    **hint,
                }
                return df, meta
            except reader.CannotParse as exc:
                self.unified_callbacks.trigger(
                    CallbackEvent.SYSTEM_WARNING,
                    reader.format_name,
                    {"warning": str(exc)},
                )
                continue
        raise UnsupportedFormatError(file_path)
