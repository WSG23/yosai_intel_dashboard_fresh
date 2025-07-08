from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd

from services.upload.protocols import UploadStorageProtocol
from services.interfaces import (
    DeviceLearningServiceProtocol,
    UploadDataServiceProtocol,
)


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


class FakeUploadDataService(UploadDataServiceProtocol):
    def __init__(self, store: FakeUploadStore) -> None:
        self.store = store

    def get_uploaded_data(self) -> Dict[str, pd.DataFrame]:
        return self.store.get_all_data()

    def get_uploaded_filenames(self) -> List[str]:
        return self.store.get_filenames()

    def clear_uploaded_data(self) -> None:
        self.store.clear_all()

    def get_file_info(self) -> Dict[str, Dict[str, Any]]:
        return self.store.get_file_info()

    def load_dataframe(self, filename: str) -> pd.DataFrame:
        df = self.store.load_dataframe(filename)
        if df is None:
            raise FileNotFoundError(filename)
        return df


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


class FakeUploadDataService(UploadDataServiceProtocol):
    def __init__(self) -> None:
        self.store: Dict[str, pd.DataFrame] = {}

    def get_uploaded_data(self) -> Dict[str, pd.DataFrame]:
        return self.store.copy()

    def get_uploaded_filenames(self) -> List[str]:
        return list(self.store.keys())

    def clear_uploaded_data(self) -> None:
        self.store.clear()

    def get_file_info(self) -> Dict[str, Dict[str, Any]]:
        return {name: {"rows": len(df)} for name, df in self.store.items()}

    def load_dataframe(self, filename: str) -> pd.DataFrame:
        return self.store.get(filename, pd.DataFrame())


class FakeColumnVerifier(ColumnVerifierProtocol):
    def create_column_verification_modal(self, file_info: Dict[str, Any]) -> Any:
        return {"modal": file_info}

    def register_callbacks(self, manager: Any, controller: Any | None = None) -> None:
        pass


class FakeConfigurationService(ConfigurationServiceProtocol):
    def __init__(self, max_mb: int = 50) -> None:
        self.max_mb = max_mb

    def get_max_upload_size_mb(self) -> int:
        return self.max_mb

    def get_max_upload_size_bytes(self) -> int:
        return self.max_mb * 1024 * 1024


class FakeUnicodeProcessor(UnicodeProcessorProtocol):
    def clean_text(self, text: str, replacement: str = "") -> str:
        return text.replace("\ud800", replacement).replace("\udfff", replacement)

    def safe_encode_text(self, value: Any) -> str:
        return str(value) if value is not None else ""

    def safe_decode_text(self, data: bytes, encoding: str = "utf-8") -> str:
        try:
            return data.decode(encoding, errors="ignore")
        except Exception:
            return ""


class FakeGraphs:
    """Minimal graphs substitute used in tests."""

    GRAPH_FIGURES: dict[str, Any] = {}

