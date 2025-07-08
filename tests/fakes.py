from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd

from services.upload.protocols import UploadStorageProtocol
from services.interfaces import DeviceLearningServiceProtocol

class FakeUploadStore(UploadStorageProtocol):
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


class FakeDeviceLearningService(DeviceLearningServiceProtocol):
    def __init__(self) -> None:
        self.saved: Dict[str, Dict[str, Any]] = {}

    def get_learned_mappings(self, df: pd.DataFrame, filename: str) -> Dict[str, Dict]:
        return {}

    def apply_learned_mappings_to_global_store(self, df: pd.DataFrame, filename: str) -> bool:
        return False

    def get_user_device_mappings(self, filename: str) -> Dict[str, Any]:
        return self.saved.get(filename, {})

    def save_user_device_mappings(self, df: pd.DataFrame, filename: str, user_mappings: Dict[str, Any]) -> bool:
        self.saved[filename] = user_mappings
        return True
