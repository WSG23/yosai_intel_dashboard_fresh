from __future__ import annotations

from typing import Any, Dict, Protocol, List

import pandas as pd


class UploadValidatorProtocol(Protocol):
    """Interface for client-side style upload validators."""

    def validate(self, filename: str, content: str) -> tuple[bool, str]:
        ...

    def to_json(self) -> str:
        ...


class ExportServiceProtocol(Protocol):
    """Interface for exporting learned mapping data."""

    def get_enhanced_data(self) -> Dict[str, Any]:
        ...

    def to_csv_string(self, data: Dict[str, Any]) -> str:
        ...

    def to_json_string(self, data: Dict[str, Any]) -> str:
        ...


class DoorMappingServiceProtocol(Protocol):
    """Interface for door/device mapping services."""

    def process_uploaded_data(
        self, df: pd.DataFrame, client_profile: str = "auto"
    ) -> Dict[str, Any]:
        ...

    def apply_learned_mappings(self, df: pd.DataFrame, filename: str) -> bool:
        ...

    def save_confirmed_mappings(
        self, df: pd.DataFrame, filename: str, confirmed_devices: List[Dict[str, Any]]
    ) -> str:
        ...


# ---------------------------------------------------------------------------
# Helper accessors
# ---------------------------------------------------------------------------
from core.enhanced_container import ServiceContainer


def _get_container(container: ServiceContainer | None = None) -> ServiceContainer | None:
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
    from services.upload.validators import ClientSideValidator

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


__all__ = [
    "UploadValidatorProtocol",
    "ExportServiceProtocol",
    "DoorMappingServiceProtocol",
    "get_upload_validator",
    "get_export_service",
    "get_door_mapping_service",
]
