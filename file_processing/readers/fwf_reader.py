from __future__ import annotations
from core.truly_unified_callbacks import TrulyUnifiedCallbacks

import pandas as pd

from .base import BaseReader
from core.unified_callbacks import CallbackEvent
from analytics_core.callbacks.unified_callback_manager import CallbackManager
from core.protocols import UnicodeProcessorProtocol


class FWFReader(BaseReader):
    """Read fixed-width formatted files."""

    format_name = "fwf"

    def __init__(
        self, *, unicode_processor: UnicodeProcessorProtocol | None = None
    ) -> None:
        super().__init__(unicode_processor=unicode_processor)
        self.unified_callbacks = CallbackManager()

    def read(self, file_path: str, hint: dict | None = None) -> pd.DataFrame:
        hint = hint or {}
        if not str(file_path).lower().endswith(".fwf"):
            raise FWFReader.CannotParse("extension mismatch")
        try:
            df = pd.read_fwf(file_path, **hint)
        except Exception as exc:
            raise FWFReader.CannotParse(str(exc)) from exc

        ratio = CSVReader._control_char_ratio(df)
        if ratio > 0.1:
            self.unified_callbacks.trigger(
                CallbackEvent.SYSTEM_WARNING,
                file_path,
                {"warning": "ControlCharWarning", "ratio": ratio},
            )
        return self._sanitize(df)


from .csv_reader import CSVReader
