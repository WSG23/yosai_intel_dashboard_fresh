from __future__ import annotations

import pandas as pd

from core.callback_events import CallbackEvent
from core.truly_unified_callbacks import TrulyUnifiedCallbacks
from core.protocols import UnicodeProcessorProtocol
from core.truly_unified_callbacks import TrulyUnifiedCallbacks
from utils.pandas_readers import read_fwf

from .base import BaseReader


class FWFReader(BaseReader):
    """Read fixed-width formatted files."""

    format_name = "fwf"

    def __init__(
        self, *, unicode_processor: UnicodeProcessorProtocol | None = None
    ) -> None:
        super().__init__(unicode_processor=unicode_processor)
        self.unified_callbacks = TrulyUnifiedCallbacks()

    def read(self, file_path: str, hint: dict | None = None) -> pd.DataFrame:
        hint = hint or {}
        if not str(file_path).lower().endswith(".fwf"):
            raise FWFReader.CannotParse("extension mismatch")
        try:
            df = read_fwf(file_path, **hint)
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
