from __future__ import annotations

import json
import pandas as pd

from .base import BaseReader
from core.callback_controller import CallbackController, CallbackEvent


class JSONReader(BaseReader):
    """Read JSON or JSON lines files."""

    format_name = "json"

    def __init__(self) -> None:
        self.callback_controller = CallbackController()

    def read(self, file_path: str, hint: dict | None = None) -> pd.DataFrame:
        hint = hint or {}
        if not str(file_path).lower().endswith(".json"):
            raise JSONReader.CannotParse("extension mismatch")
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as fh:
                text = fh.read()
            try:
                data = json.loads(text)
                df = pd.json_normalize(data)
            except json.JSONDecodeError:
                df = pd.read_json(text, lines=True)
        except Exception as exc:
            raise JSONReader.CannotParse(str(exc)) from exc

        ratio = CSVReader._control_char_ratio(df)
        if ratio > 0.1:
            self.callback_controller.fire_event(
                CallbackEvent.SYSTEM_WARNING,
                file_path,
                {"warning": "ControlCharWarning", "ratio": ratio},
            )
        return self._sanitize(df)


from .csv_reader import CSVReader

