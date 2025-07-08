from __future__ import annotations

import pandas as pd

from .base import BaseReader
from core.callback_controller import CallbackEvent
from core.callback_manager import CallbackManager
from core.protocols import UnicodeProcessorProtocol


class ExcelReader(BaseReader):
    """Read Excel files (xls/xlsx)."""

    format_name = "excel"

    def __init__(self, *, unicode_processor: UnicodeProcessorProtocol | None = None) -> None:
        super().__init__(unicode_processor=unicode_processor)
        self.callback_controller = CallbackManager()

    def read(self, file_path: str, hint: dict | None = None) -> pd.DataFrame:
        if not str(file_path).lower().endswith(('.xls', '.xlsx')):
            raise ExcelReader.CannotParse("extension mismatch")
        try:
            df = pd.read_excel(file_path, **(hint or {}))
        except Exception as exc:
            raise ExcelReader.CannotParse(str(exc)) from exc

        ratio = CSVReader._control_char_ratio(df)
        if ratio > 0.1:
            self.callback_controller.trigger(
                CallbackEvent.SYSTEM_WARNING,
                file_path,
                {"warning": "ControlCharWarning", "ratio": ratio},
            )
        return self._sanitize(df)


from .csv_reader import CSVReader

