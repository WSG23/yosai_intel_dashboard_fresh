from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

import pandas as pd

from core.callback_controller import CallbackController, CallbackEvent
from .format_detector import FormatDetector, UnsupportedFormatError
from .readers import ArchiveReader, CSVReader, ExcelReader, FWFReader, JSONReader


class DataProcessor:
    """Process input files using ``FormatDetector`` and apply transformations."""

    def __init__(self, readers: Optional[list] = None, hint: Optional[Dict] = None) -> None:
        self.format_detector = FormatDetector(
            readers or [CSVReader(), JSONReader(), ExcelReader(), FWFReader(), ArchiveReader()]
        )
        self.hint = hint or {}
        self.pipeline_metadata: Dict[str, Dict] = {}
        self.callback_controller = CallbackController()

    def load_file(self, file_path: str) -> pd.DataFrame:
        try:
            df_raw, meta = self.format_detector.detect_and_load(file_path, hint=self.hint)
            self.pipeline_metadata["last_ingest"] = meta
            return df_raw
        except UnsupportedFormatError as exc:
            self.callback_controller.fire_event(
                CallbackEvent.SYSTEM_ERROR,
                file_path,
                {"error": str(exc)},
            )
            raise

    # Placeholder for additional processing steps
    def process(self, file_path: str) -> pd.DataFrame:
        return self.load_file(file_path)

