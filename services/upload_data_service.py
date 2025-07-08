import logging
from typing import Any, Dict, List

import pandas as pd

from services.interfaces import UploadDataServiceProtocol
from utils.upload_store import uploaded_data_store, UploadedDataStore


logger = logging.getLogger(__name__)


class UploadDataService(UploadDataServiceProtocol):
    """Concrete service providing access to uploaded data via a store."""

    def __init__(self, store: UploadedDataStore = uploaded_data_store) -> None:
        self.store = store

    def get_uploaded_data(self) -> Dict[str, pd.DataFrame]:
        return self.store.get_all_data()

    def get_uploaded_filenames(self) -> List[str]:
        return self.store.get_filenames()

    def clear_uploaded_data(self) -> None:
        self.store.clear_all()
        logger.info("Uploaded data cleared")

    def get_file_info(self) -> Dict[str, Dict[str, Any]]:
        return self.store.get_file_info()

    def load_dataframe(self, filename: str) -> pd.DataFrame:
        return self.store.load_dataframe(filename)


# Default service used by module-level helper functions
_default_service = UploadDataService()


def get_uploaded_data() -> Dict[str, pd.DataFrame]:
    return _default_service.get_uploaded_data()


def get_uploaded_filenames() -> List[str]:
    return _default_service.get_uploaded_filenames()


def clear_uploaded_data() -> None:
    _default_service.clear_uploaded_data()


def get_file_info() -> Dict[str, Dict[str, Any]]:
    return _default_service.get_file_info()


def load_dataframe(filename: str) -> pd.DataFrame:
    return _default_service.load_dataframe(filename)


__all__ = [
    "UploadDataService",
    "get_uploaded_data",
    "get_uploaded_filenames",
    "clear_uploaded_data",
    "get_file_info",
    "load_dataframe",
]
