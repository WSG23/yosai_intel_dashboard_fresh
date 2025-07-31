from __future__ import annotations

import pandas as pd

from yosai_intel_dashboard.src.infrastructure.callbacks.events import CallbackEvent
from yosai_intel_dashboard.src.infrastructure.callbacks.unified_callbacks import TrulyUnifiedCallbacks
from yosai_intel_dashboard.src.core.interfaces.protocols import UnicodeProcessorProtocol
from yosai_intel_dashboard.src.infrastructure.callbacks.unified_callbacks import TrulyUnifiedCallbacks
from yosai_intel_dashboard.src.utils.pandas_readers import read_csv

from .base import BaseReader


class CSVReader(BaseReader):
    """Read comma separated value files."""

    format_name = "csv"

    def __init__(
        self, *, unicode_processor: UnicodeProcessorProtocol | None = None
    ) -> None:
        super().__init__(unicode_processor=unicode_processor)
        self.unified_callbacks = TrulyUnifiedCallbacks()

    def read(self, file_path: str, hint: dict | None = None) -> pd.DataFrame:
        hint = hint or {}
        if not str(file_path).lower().endswith(".csv"):
            raise CSVReader.CannotParse("extension mismatch")
        try:
            df = read_csv(file_path, **hint)
        except Exception as exc:
            raise CSVReader.CannotParse(str(exc)) from exc

        control_ratio = self._control_char_ratio(df)
        if control_ratio > 0.1:
            self.unified_callbacks.trigger(
                CallbackEvent.SYSTEM_WARNING,
                file_path,
                {"warning": "ControlCharWarning", "ratio": control_ratio},
            )

        return self._sanitize(df)

    @staticmethod
    def _control_char_ratio(df: pd.DataFrame) -> float:
        text = "".join(
            df[col].dropna().astype(str).str.cat(sep="")
            for col in df.select_dtypes(include="object").columns
        )
        if not text:
            return 0.0
        ctrl = sum(1 for ch in text if ord(ch) < 32 or ord(ch) == 127)
        return ctrl / len(text)
