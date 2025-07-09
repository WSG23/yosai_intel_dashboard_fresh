#!/usr/bin/env python3
from __future__ import annotations
"""File upload page wiring the reusable upload component."""

import logging
import types
from typing import TYPE_CHECKING, Any

from dash import html

try:  # Lazy import for optional heavy dependencies
    from components.upload import UnifiedUploadComponent
except Exception as exc:  # pragma: no cover - optional dependency missing
    UnifiedUploadComponent = None  # type: ignore[assignment]
    _import_error = exc
else:
    _import_error = None

if TYPE_CHECKING:  # pragma: no cover - import for type checking only
    from dash import html as Html

    from core.truly_unified_callbacks import (
        TrulyUnifiedCallbacks as TrulyUnifiedCallbacksType,
    )
else:  # pragma: no cover - fallback type alias
    Html = html  # type: ignore[assignment]
    TrulyUnifiedCallbacksType = Any


logger = logging.getLogger(__name__)

# Single shared instance for this page
_upload_component = UnifiedUploadComponent() if UnifiedUploadComponent else None


def load_page(controller=None, queue_manager=None):
    """Return page helpers with optional dependency injection."""

    component = UnifiedUploadComponent() if UnifiedUploadComponent else None

    def _layout() -> Html.Div:
        if component:
            return html.Div(
                [html.H2("File Upload"), component.layout()],
                className="page-container",
            )
        return html.Div("Upload component unavailable")

    def _register_callbacks(manager: TrulyUnifiedCallbacksType) -> None:
        if component:
            component.register_callbacks(manager, controller)

    return types.SimpleNamespace(
        layout=_layout,
        register_callbacks=_register_callbacks,
        check_upload_system_health=check_upload_system_health,
    )


def layout() -> Html.Div:
    """Return the upload page layout wrapped in a container."""
    if _upload_component:
        return html.Div(
            [html.H2("File Upload"), _upload_component.layout()],
            className="page-container",
        )
    return html.Div("Upload component unavailable")


def register_callbacks(manager: TrulyUnifiedCallbacksType, controller=None) -> None:
    """Register upload callbacks using the underlying component."""
    if _upload_component:
        _upload_component.register_callbacks(manager, controller)


register_upload_callbacks = register_callbacks


def check_upload_system_health() -> dict:
    """Simple health check for the upload page."""
    if _import_error:
        logger.error("Upload component failed to load: %s", _import_error)
    status = "healthy" if _import_error is None else "degraded"
    return {
        "status": status,
        "components": [
            (
                "Upload component loaded"
                if _import_error is None
                else "Upload component missing"
            )
        ],
        "errors": [] if _import_error is None else [str(_import_error)],
    }


__all__ = [
    "layout",
    "register_upload_callbacks",
    "register_callbacks",
    "check_upload_system_health",
    "load_page",
]
