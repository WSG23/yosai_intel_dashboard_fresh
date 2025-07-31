from __future__ import annotations

import pandas as pd

from yosai_intel_dashboard.src.infrastructure.callbacks.events import CallbackEvent
from yosai_intel_dashboard.src.infrastructure.callbacks.unified_callbacks import TrulyUnifiedCallbacks
from yosai_intel_dashboard.src.core.interfaces.protocols import UnicodeProcessorProtocol
from yosai_intel_dashboard.src.infrastructure.callbacks.unified_callbacks import TrulyUnifiedCallbacks
from yosai_intel_dashboard.src.utils.pandas_readers import read_excel

from .base import BaseReader


class ExcelReader(BaseReader):
    """Read Excel files (xls/xlsx)."""

    format_name = "excel"

    def __init__(
        self, *, unicode_processor: UnicodeProcessorProtocol | None = None
    ) -> None:
        super().__init__(unicode_processor=unicode_processor)
        self.unified_callbacks = TrulyUnifiedCallbacks()

    def read(self, file_path: str, hint: dict | None = None) -> pd.DataFrame:
        if not str(file_path).lower().endswith((".xls", ".xlsx")):
            raise ExcelReader.CannotParse("extension mismatch")
        try:
            df = read_excel(file_path, **(hint or {}))
        except Exception as exc:
            raise ExcelReader.CannotParse(str(exc)) from exc

        ratio = CSVReader._control_char_ratio(df)
        if ratio > 0.1:
            self.unified_callbacks.trigger(
                CallbackEvent.SYSTEM_WARNING,
                file_path,
                {"warning": "ControlCharWarning", "ratio": ratio},
            )
        return self._sanitize(df)


from .csv_reader import CSVReader
