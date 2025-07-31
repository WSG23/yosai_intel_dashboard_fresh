from __future__ import annotations

from typing import Any, Dict, List, Protocol, runtime_checkable

from mapping.core.interfaces import ProcessorInterface, StorageInterface
from mapping.core.models import MappingData

import pandas as pd

from core.service_container import ServiceContainer


@runtime_checkable
class UploadValidatorProtocol(Protocol):
    """Interface for client-side style upload validators."""

    def validate(self, filename: str, content: str) -> tuple[bool, str]: ...

    def to_json(self) -> str: ...


@runtime_checkable
class ExportServiceProtocol(Protocol):
    """Interface for exporting learned mapping data."""

    def get_enhanced_data(self) -> Dict[str, Any]: ...

    def to_csv_string(self, data: Dict[str, Any]) -> str: ...

    def to_json_string(self, data: Dict[str, Any]) -> str: ...


@runtime_checkable
class DoorMappingServiceProtocol(Protocol):
    """Interface for door/device mapping services."""

    def process_uploaded_data(
        self, df: pd.DataFrame, client_profile: str = "auto"
    ) -> Dict[str, Any]: ...

    def apply_learned_mappings(self, df: pd.DataFrame, filename: str) -> bool: ...

    def save_confirmed_mappings(
        self, df: pd.DataFrame, filename: str, confirmed_devices: List[Dict[str, Any]]
    ) -> str: ...


@runtime_checkable
class DeviceLearningServiceProtocol(Protocol):
    """Interface for persistent device learning services."""

    def get_learned_mappings(
        self, df: pd.DataFrame, filename: str
    ) -> Dict[str, Dict]: ...

    def apply_learned_mappings_to_global_store(
        self, df: pd.DataFrame, filename: str
    ) -> bool: ...

    def get_user_device_mappings(self, filename: str) -> Dict[str, Any]: ...

    def save_user_device_mappings(
        self, df: pd.DataFrame, filename: str, user_mappings: Dict[str, Any]
    ) -> bool: ...


# ---------------------------------------------------------------------------
# Helper accessors
# ---------------------------------------------------------------------------
# Use the same ServiceContainer implementation as ``core.app_factory``
# to avoid type mismatches when helpers are accessed through the
# application-wide dependency injection container.


def _get_container(
    container: ServiceContainer | None = None,
) -> ServiceContainer | None:
    if container is not None:
        return container
    try:  # pragma: no cover - dash may be missing in tests
        from dash import get_app

        app = get_app()
        return getattr(app, "_service_container", None)
    except Exception:
        return None


def get_upload_validator(
    container: ServiceContainer | None = None,
) -> UploadValidatorProtocol:
    c = _get_container(container)
    if c and c.has("upload_validator"):
        return c.get("upload_validator")
    from services.upload.validator import ClientSideValidator

    return ClientSideValidator()


def get_export_service(
    container: ServiceContainer | None = None,
) -> ExportServiceProtocol:
    c = _get_container(container)
    if c and c.has("export_service"):
        return c.get("export_service")
    import services.export_service as svc

    return svc


def get_door_mapping_service(
    container: ServiceContainer | None = None,
) -> DoorMappingServiceProtocol:
    c = _get_container(container)
    if c and c.has("door_mapping_service"):
        return c.get("door_mapping_service")
    from services.door_mapping_service import door_mapping_service

    return door_mapping_service


def get_device_learning_service(
    container: ServiceContainer | None = None,
) -> "DeviceLearningService":
    """Return the registered :class:`DeviceLearningService` instance."""
    c = _get_container(container)
    if c and c.has("device_learning_service"):
        return c.get("device_learning_service")
    from services.device_learning_service import create_device_learning_service

    return create_device_learning_service()


def get_upload_data_service(
    container: ServiceContainer | None = None,
) -> UploadDataServiceProtocol:
    """Return the registered :class:`UploadDataServiceProtocol` instance."""
    c = _get_container(container)
    if c and c.has("upload_data_service"):
        return c.get("upload_data_service")
    from services.upload_data_service import UploadDataService as UploadDataSvc
    from utils.upload_store import uploaded_data_store

    return UploadDataSvc(uploaded_data_store)


def get_mapping_service(
    container: ServiceContainer | None = None,
) -> "MappingServiceProtocol":
    """Return the registered :class:`MappingServiceProtocol` instance."""
    c = _get_container(container)
    if c and c.has("mapping_service"):
        return c.get("mapping_service")
    from mapping.factories.service_factory import create_mapping_service

    return create_mapping_service(container=c)


__all__ = [
    "UploadValidatorProtocol",
    "ExportServiceProtocol",
    "DoorMappingServiceProtocol",
    "DeviceLearningServiceProtocol",
    "UploadDataStoreProtocol",
    "UploadDataServiceProtocol",
    "MappingServiceProtocol",
    "get_upload_validator",
    "get_export_service",
    "get_door_mapping_service",
    "get_device_learning_service",
    "get_upload_data_service",
    "get_mapping_service",
    "AnalyticsDataLoaderProtocol",
    "DatabaseAnalyticsRetrieverProtocol",
    "get_analytics_data_loader",
    "get_database_analytics_retriever",
]


@runtime_checkable
class UploadDataStoreProtocol(Protocol):
    """Interface for simple upload data stores."""

    def get_upload_data(self) -> Dict[str, Any]: ...
    def store_upload_data(self, data: Dict[str, Any]) -> bool: ...
    def clear_data(self) -> None: ...


@runtime_checkable
class UploadDataServiceProtocol(Protocol):
    """Interface for accessing uploaded dataframes."""

    def get_uploaded_data(self) -> Dict[str, pd.DataFrame]: ...

    def get_uploaded_filenames(self) -> List[str]: ...

    def clear_uploaded_data(self) -> None: ...

    def get_file_info(self) -> Dict[str, Dict[str, Any]]: ...

    def load_dataframe(self, filename: str) -> pd.DataFrame: ...

    def load_mapping(self, filename: str) -> Dict[str, Any]: ...

    def save_mapping(self, filename: str, mapping: Dict[str, Any]) -> None: ...


@runtime_checkable
class MappingServiceProtocol(Protocol):
    """Interface for mapping services."""

    column_proc: ProcessorInterface
    device_proc: ProcessorInterface

    def process_upload(
        self, df: pd.DataFrame, filename: str, *, model_key: str | None = None
    ) -> MappingData: ...


@runtime_checkable
class DeviceLearningServiceProtocol(Protocol):
    """Interface for device learning services."""

    def get_user_device_mappings(self, filename: str) -> Dict[str, Any]: ...
    def save_device_mappings(self, mappings: Dict[str, Any]) -> bool: ...
    def learn_from_data(self, df: pd.DataFrame) -> Dict[str, Any]: ...


@runtime_checkable
class AnalyticsDataLoaderProtocol(Protocol):
    """Interface for analytics data loaders."""

    def load_uploaded_data(self) -> Dict[str, pd.DataFrame]: ...

    def clean_uploaded_dataframe(self, df: pd.DataFrame) -> pd.DataFrame: ...

    def summarize_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]: ...

    def analyze_with_chunking(
        self, df: pd.DataFrame, analysis_types: List[str]
    ) -> Dict[str, Any]: ...

    def diagnose_data_flow(self, df: pd.DataFrame) -> Dict[str, Any]: ...

    def get_real_uploaded_data(self) -> Dict[str, Any]: ...

    def get_analytics_with_fixed_processor(self) -> Dict[str, Any]: ...

    def load_patterns_dataframe(
        self, data_source: str | None
    ) -> tuple[pd.DataFrame, int]: ...


@runtime_checkable
class DatabaseAnalyticsRetrieverProtocol(Protocol):
    """Interface for retrieving analytics from a database."""

    def get_analytics(self) -> Dict[str, Any]: ...


def get_analytics_data_loader(
    controller: "UploadProcessingController",  # type: ignore[str-format]
    processor: "Processor",
    container: ServiceContainer | None = None,
) -> AnalyticsDataLoaderProtocol:
    c = _get_container(container)
    if c and c.has("data_loader"):
        return c.get("data_loader")
    from services.analytics.data.loader import DataLoader

    return DataLoader(controller, processor)


def get_database_analytics_retriever(
    helper: "DatabaseAnalyticsHelper",
    container: ServiceContainer | None = None,
) -> DatabaseAnalyticsRetrieverProtocol:
    c = _get_container(container)
    if c and c.has("database_analytics_retriever"):
        return c.get("database_analytics_retriever")
    from services.database_retriever import DatabaseAnalyticsRetriever

    return DatabaseAnalyticsRetriever(helper)
