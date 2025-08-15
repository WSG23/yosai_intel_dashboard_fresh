from __future__ import annotations

import pandas as pd

from yosai_intel_dashboard.src.infrastructure.callbacks.events import CallbackEvent
from yosai_intel_dashboard.src.utils.pandas_readers import read_json as util_read_json

from .base import BaseReader


class JSONReader(BaseReader):
    """Read JSON or JSON lines files."""

    format_name = "json"

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
