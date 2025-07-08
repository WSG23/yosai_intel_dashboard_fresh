from __future__ import annotations

from typing import Any, Dict, List, Protocol, runtime_checkable

import pandas as pd


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


@runtime_checkable
class UploadDataServiceProtocol(Protocol):
    """Interface for accessing uploaded data."""

    def get_uploaded_data(self) -> Dict[str, pd.DataFrame]:
        """Return all uploaded dataframes."""
        ...

    def get_uploaded_filenames(self) -> List[str]:
        """Return names of uploaded files."""
        ...

    def clear_uploaded_data(self) -> None:
        """Remove all uploaded data."""
        ...

    def get_file_info(self) -> Dict[str, Dict[str, Any]]:
        """Return info dictionary for uploaded files."""
        ...

    def load_dataframe(self, filename: str) -> pd.DataFrame:
        """Load a specific uploaded dataframe."""
        ...


# ---------------------------------------------------------------------------
# Helper accessors
# ---------------------------------------------------------------------------
from core.enhanced_container import ServiceContainer


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
    from services.upload.core.validator import ClientSideValidator

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
    """Return the registered :class:`UploadDataService` instance."""
    c = _get_container(container)
    if c and c.has("upload_data_service"):
        return c.get("upload_data_service")
    from services.upload_data_service import UploadDataService
    from utils.upload_store import uploaded_data_store

    return UploadDataService(uploaded_data_store)


__all__ = [
    "UploadValidatorProtocol",
    "ExportServiceProtocol",
    "DoorMappingServiceProtocol",
    "DeviceLearningServiceProtocol",
    "UploadDataServiceProtocol",
    "get_upload_validator",
    "get_export_service",
    "get_door_mapping_service",
    "get_device_learning_service",
    "get_upload_data_service",
]
