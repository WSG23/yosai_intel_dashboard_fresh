import logging
from typing import Any, Dict, List

import pandas as pd

from services.interfaces import (
    UploadDataServiceProtocol,
    get_upload_data_service,
)
from core.service_container import ServiceContainer
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

def _resolve_service(
    service: UploadDataServiceProtocol | None,
    container: ServiceContainer | None,
) -> UploadDataServiceProtocol:
    if service is not None:
        return service
    return get_upload_data_service(container)


def get_uploaded_data(
    service: UploadDataServiceProtocol | None = None,
    container: ServiceContainer | None = None,
) -> Dict[str, pd.DataFrame]:
    svc = _resolve_service(service, container)
    return svc.get_uploaded_data()


def get_uploaded_filenames(
    service: UploadDataServiceProtocol | None = None,
    container: ServiceContainer | None = None,
) -> List[str]:
    svc = _resolve_service(service, container)
    return svc.get_uploaded_filenames()


def clear_uploaded_data(
    service: UploadDataServiceProtocol | None = None,
    container: ServiceContainer | None = None,
) -> None:
    svc = _resolve_service(service, container)
    svc.clear_uploaded_data()


def get_file_info(
    service: UploadDataServiceProtocol | None = None,
    container: ServiceContainer | None = None,
) -> Dict[str, Dict[str, Any]]:
    svc = _resolve_service(service, container)
    return svc.get_file_info()


def load_dataframe(
    filename: str,
    service: UploadDataServiceProtocol | None = None,
    container: ServiceContainer | None = None,
) -> pd.DataFrame:
    svc = _resolve_service(service, container)
    return svc.load_dataframe(filename)


__all__ = [
    "UploadDataService",
    "get_uploaded_data",
    "get_uploaded_filenames",
    "clear_uploaded_data",
    "get_file_info",
    "load_dataframe",
]
