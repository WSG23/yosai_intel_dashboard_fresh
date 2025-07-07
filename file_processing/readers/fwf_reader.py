from __future__ import annotations

import pandas as pd

from .base import BaseReader
from core.callback_controller import CallbackController, CallbackEvent


class FWFReader(BaseReader):
    """Read fixed-width formatted files."""

    format_name = "fwf"

    def __init__(self) -> None:
        self.callback_controller = CallbackController()

    def read(self, file_path: str, hint: dict | None = None) -> pd.DataFrame:
        hint = hint or {}
        if not str(file_path).lower().endswith('.fwf'):
            raise FWFReader.CannotParse("extension mismatch")
        try:
            df = pd.read_fwf(file_path, **hint)
        except Exception as exc:
            raise FWFReader.CannotParse(str(exc)) from exc

        ratio = CSVReader._control_char_ratio(df)
        if ratio > 0.1:
            self.callback_controller.fire_event(
                CallbackEvent.SYSTEM_WARNING,
                file_path,
                {"warning": "ControlCharWarning", "ratio": ratio},
            )
        return self._sanitize(df)


from .csv_reader import CSVReader

