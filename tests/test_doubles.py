from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd

from core.protocols import UnicodeProcessorProtocol
from yosai_intel_dashboard.src.services.upload.protocols import UploadStorageProtocol


class SimpleUnicodeProcessor(UnicodeProcessorProtocol):
    """Minimal Unicode processor used for tests."""

    def clean_text(self, text: str, replacement: str = "") -> str:
        return text.replace("\ud800", replacement).replace("\udfff", replacement)

    def safe_encode_text(self, value: Any) -> str:
        return "" if value is None else str(value)

    def safe_decode_text(self, data: bytes, encoding: str = "utf-8") -> str:
        try:
            return data.decode(encoding, errors="ignore")
        except Exception:
            return ""


class InMemoryUploadStore(UploadStorageProtocol):
    """Simple in-memory upload storage used for tests."""

    def __init__(self) -> None:
        self.data: Dict[str, pd.DataFrame] = {}
        self.info: Dict[str, Dict[str, Any]] = {}

    def add_file(self, filename: str, dataframe: pd.DataFrame) -> None:
        self.data[filename] = dataframe
        self.info[filename] = {
            "rows": len(dataframe),
            "columns": len(dataframe.columns),
        }

    def get_all_data(self) -> Dict[str, pd.DataFrame]:
        return self.data.copy()

    def clear_all(self) -> None:
        self.data.clear()
        self.info.clear()

    def load_dataframe(self, filename: str) -> pd.DataFrame | None:
        return self.data.get(filename)

    def get_filenames(self) -> List[str]:
        return list(self.data.keys())

    def get_file_info(self) -> Dict[str, Dict[str, Any]]:
        return self.info.copy()

    def wait_for_pending_saves(self) -> None:  # pragma: no cover - no async ops
        pass
