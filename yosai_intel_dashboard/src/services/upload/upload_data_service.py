"""Service helpers for accessing uploaded data from the store."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

try:
    from typing import override
except ImportError:  # pragma: no cover - for Python <3.12

    from typing_extensions import override

import pandas as pd

from yosai_intel_dashboard.src.core.interfaces.service_protocols import (
    UploadDataServiceProtocol,
    get_upload_data_service,
)
from yosai_intel_dashboard.src.infrastructure.di.service_container import (
    ServiceContainer,
)
from yosai_intel_dashboard.src.utils.sanitization import sanitize_filename
from yosai_intel_dashboard.src.utils.upload_store import (
    UploadedDataStore,
    get_uploaded_data_store,
)

logger = logging.getLogger(__name__)


class UploadDataService(UploadDataServiceProtocol):
    """Concrete service providing access to uploaded data via a store."""

    def __init__(self, store: UploadedDataStore | None = None) -> None:
        """Initialize the service with the given ``UploadedDataStore``."""
        self.store = store or get_uploaded_data_store()

    @override
    def get_uploaded_data(self) -> Dict[str, pd.DataFrame]:
        return self.store.get_all_data()

    @override
    def get_uploaded_filenames(self) -> List[str]:
        return self.store.get_filenames()

    @override
    def clear_uploaded_data(self) -> None:
        self.store.clear_all()
        logger.info("Uploaded data cleared")

    @override
    def get_file_info(self) -> Dict[str, Dict[str, Any]]:
        return self.store.get_file_info()

    @override
    def load_dataframe(self, filename: str) -> pd.DataFrame:
        safe_name = sanitize_filename(filename)
        return self.store.load_dataframe(safe_name)

    @override
    def load_mapping(self, filename: str) -> Dict[str, Any]:
        safe_name = sanitize_filename(filename)
        return self.store.load_mapping(safe_name)

    @override
    def save_mapping(self, filename: str, mapping: Dict[str, Any]) -> None:
        safe_name = sanitize_filename(filename)
        self.store.save_mapping(safe_name, mapping)


def _resolve_service(
    service: UploadDataServiceProtocol | None,
    container: ServiceContainer | None,
) -> UploadDataServiceProtocol:
    """Return a service instance from ``service`` or the DI ``container``."""
    if service is not None:
        return service
    return get_upload_data_service(container)


def get_uploaded_data(
    service: UploadDataServiceProtocol | None = None,
    container: ServiceContainer | None = None,
) -> Dict[str, pd.DataFrame]:
    """Return all uploaded dataframes using the resolved service."""
    svc = _resolve_service(service, container)
    return svc.get_uploaded_data()


def get_uploaded_filenames(
    service: UploadDataServiceProtocol | None = None,
    container: ServiceContainer | None = None,
) -> List[str]:
    """Return list of uploaded filenames using the resolved service."""
    svc = _resolve_service(service, container)
    return svc.get_uploaded_filenames()


def clear_uploaded_data(
    service: UploadDataServiceProtocol | None = None,
    container: ServiceContainer | None = None,
) -> None:
    """Delete all uploaded data using the resolved service."""
    svc = _resolve_service(service, container)
    svc.clear_uploaded_data()


def get_file_info(
    service: UploadDataServiceProtocol | None = None,
    container: ServiceContainer | None = None,
) -> Dict[str, Dict[str, Any]]:
    """Return metadata for uploaded files using the resolved service."""
    svc = _resolve_service(service, container)
    return svc.get_file_info()


def load_dataframe(
    filename: str,
    service: UploadDataServiceProtocol | None = None,
    container: ServiceContainer | None = None,
) -> pd.DataFrame:
    """Load the uploaded DataFrame ``filename`` using the resolved service."""
    svc = _resolve_service(service, container)
    return svc.load_dataframe(filename)


def load_mapping(
    filename: str,
    service: UploadDataServiceProtocol | None = None,
    container: ServiceContainer | None = None,
) -> Dict[str, Any]:
    """Load the mapping information for ``filename`` using the resolved service."""
    svc = _resolve_service(service, container)
    return svc.load_mapping(filename)


def save_mapping(
    filename: str,
    mapping: Dict[str, Any],
    service: UploadDataServiceProtocol | None = None,
    container: ServiceContainer | None = None,
) -> None:
    """Persist ``mapping`` for ``filename`` using the resolved service."""
    svc = _resolve_service(service, container)
    svc.save_mapping(filename, mapping)


__all__ = [
    "UploadDataService",
    "get_uploaded_data",
    "get_uploaded_filenames",
    "clear_uploaded_data",
    "get_file_info",
    "load_dataframe",
    "load_mapping",
    "save_mapping",
]
