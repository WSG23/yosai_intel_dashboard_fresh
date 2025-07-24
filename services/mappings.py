from __future__ import annotations

from typing import Any, Dict

from core.container import container


def _ensure_services() -> None:
    """Ensure upload-related services are registered."""
    if container.has("upload_processor"):
        return
    try:  # pragma: no cover - optional registration
        from config.service_registration import register_upload_services
    except Exception:
        return

    register_upload_services(container)


def save_column_mappings(file_id: str, mappings: Dict[str, str]) -> None:
    """Persist column mappings for *file_id* using the configured service."""
    _ensure_services()
    service = container.get("consolidated_learning_service")
    service.save_column_mappings(file_id, mappings)


def save_device_mappings(file_id: str, mappings: Dict[str, Any]) -> None:
    """Persist device mappings for *file_id* using the configured service."""
    _ensure_services()
    service = container.get("device_learning_service")
    if hasattr(service, "save_device_mappings"):
        try:
            service.save_device_mappings(file_id, mappings)
            return
        except TypeError:
            pass
    if hasattr(service, "save_user_device_mapping"):
        for device_name, mapping in mappings.items():
            service.save_user_device_mapping(
                filename=file_id,
                device_name=device_name,
                device_type=mapping.get("device_type", "unknown"),
                location=mapping.get("location"),
                properties=mapping.get("properties", {}),
            )
    else:
        raise AttributeError("Device learning service missing save method")
