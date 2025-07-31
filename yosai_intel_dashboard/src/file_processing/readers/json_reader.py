from __future__ import annotations

import pandas as pd

from core.callback_events import CallbackEvent
from core.truly_unified_callbacks import TrulyUnifiedCallbacks
from core.protocols import UnicodeProcessorProtocol
from core.truly_unified_callbacks import TrulyUnifiedCallbacks
from yosai_intel_dashboard.src.utils.pandas_readers import read_json as util_read_json

from .base import BaseReader


class JSONReader(BaseReader):
    """Read JSON or JSON lines files."""

    format_name = "json"

    def __init__(
        self, *, unicode_processor: UnicodeProcessorProtocol | None = None
    ) -> None:
        super().__init__(unicode_processor=unicode_processor)
        self.unified_callbacks = TrulyUnifiedCallbacks()

    def read(self, file_path: str, hint: dict | None = None) -> pd.DataFrame:
        hint = hint or {}
        if not str(file_path).lower().endswith(".json"):
            raise JSONReader.CannotParse("extension mismatch")
        try:
            df = util_read_json(file_path)
        except Exception as exc:
            raise JSONReader.CannotParse(str(exc)) from exc

        ratio = CSVReader._control_char_ratio(df)
        if ratio > 0.1:
            self.unified_callbacks.trigger(
                CallbackEvent.SYSTEM_WARNING,
                file_path,
                {"warning": "ControlCharWarning", "ratio": ratio},
            )
        return self._sanitize(df)


from .csv_reader import CSVReader
