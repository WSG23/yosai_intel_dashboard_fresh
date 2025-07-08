#!/usr/bin/env python3
"""Advanced file upload page using the reusable component."""
from __future__ import annotations

from typing import TYPE_CHECKING

from dash import html

try:  # Lazy import to avoid heavy deps during startup
    from components.file_upload_component import FileUploadComponent
except Exception as exc:  # pragma: no cover - optional dependency missing
    FileUploadComponent = None  # type: ignore[assignment]
    _import_error = exc
else:
    _import_error = None

if TYPE_CHECKING:  # pragma: no cover - import for type checking only
    from core.truly_unified_callbacks import TrulyUnifiedCallbacks


# Single shared instance for this page
_upload_component = FileUploadComponent() if FileUploadComponent else None


def layout() -> html.Div:
    """Return the upload page layout."""
    if _upload_component:
        return _upload_component.layout()
    return html.Div("Upload component unavailable")


def register_upload_callbacks(manager: "TrulyUnifiedCallbacks", controller=None) -> None:
    """Register upload callbacks using the underlying component."""
    if _upload_component:
        _upload_component.register_callbacks(manager, controller)


# Backwards compatible aliases -------------------------------------------------

def register_enhanced_upload_callbacks(manager: "TrulyUnifiedCallbacks", controller=None) -> None:
    """Alias for older code paths."""
    register_upload_callbacks(manager, controller)


def register_callbacks(manager: "TrulyUnifiedCallbacks", controller=None) -> None:
    """Alias for compatibility with the factory."""
    register_upload_callbacks(manager, controller)


def check_upload_system_health() -> dict:
    """Simple health check for the upload page."""
    status = "healthy" if _import_error is None else "degraded"
    errors = [] if _import_error is None else [str(_import_error)]
    return {
        "status": status,
        "components": ["Advanced upload layout: OK" if _import_error is None else "Upload component missing"],
        "errors": errors,
    }


__all__ = [
    "layout",
    "register_upload_callbacks",
    "register_enhanced_upload_callbacks",
    "register_callbacks",
    "check_upload_system_health",
]
