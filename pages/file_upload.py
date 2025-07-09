#!/usr/bin/env python3
"""File upload page wiring the reusable upload component."""
from __future__ import annotations

import logging
import types
from typing import TYPE_CHECKING, Any

from dash import html, register_page

from core.callback_registry import _callback_registry
from core.unicode import safe_encode_text

try:
    from core.truly_unified_callbacks import TrulyUnifiedCallbacks
except Exception:  # pragma: no cover - fallback when unavailable
    TrulyUnifiedCallbacks = None  # type: ignore

logger = logging.getLogger(__name__)

register_page(__name__, path="/file-upload", name="File Upload", aliases=["/upload"])

_import_error: Exception | None = None


def _safe_import_upload_component():
    """Attempt to import ``UnifiedUploadComponent`` with detailed logging."""
    global _import_error
    try:
        from components.upload import UnifiedUploadComponent as UUC

        logger.debug("UnifiedUploadComponent imported successfully")
        _import_error = None
        return UUC
    except Exception as exc:  # pragma: no cover - optional dependency missing
        _import_error = exc
        logger.exception("Failed to import UnifiedUploadComponent")
        return None


UnifiedUploadComponent = _safe_import_upload_component()  # type: ignore[assignment]

if TYPE_CHECKING:  # pragma: no cover - import for type checking only
    from dash import html as Html

    from core.truly_unified_callbacks import (
        TrulyUnifiedCallbacks as TrulyUnifiedCallbacksType,
    )
else:  # pragma: no cover - fallback type alias
    Html = html  # type: ignore[assignment]
    TrulyUnifiedCallbacksType = Any


# Single shared instance for this page
_upload_component = UnifiedUploadComponent() if UnifiedUploadComponent else None


def load_page(controller=None, queue_manager=None):
    """Return page helpers with optional dependency injection."""

    component_cls = _safe_import_upload_component()
    component = component_cls() if component_cls else None

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


def safe_upload_layout():
    """Unicode-safe wrapper for upload layout.
    Prevents rendering issues that cause navbar flash."""
    try:
        # Get the original layout
        original_layout = layout()

        # Process any text content to ensure Unicode safety
        if hasattr(original_layout, "children"):
            # This is a container, process its children recursively
            def process_component(component):
                if hasattr(component, "children"):
                    if isinstance(component.children, str):
                        component.children = safe_encode_text(component.children)
                    elif isinstance(component.children, list):
                        for child in component.children:
                            process_component(child)
                return component

            original_layout = process_component(original_layout)

        return original_layout

    except Exception as e:
        # Fallback layout if original fails
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Upload layout creation failed: {e}")

        import dash_bootstrap_components as dbc
        from dash import html

        return dbc.Container(
            [
                dbc.Alert(
                    "Upload page is temporarily unavailable. Please try again later.",
                    color="warning",
                ),
                html.Div(id="upload-fallback-content"),
            ]
        )


def register_callbacks(manager: Any, controller=None) -> None:
    """Register upload callbacks using the underlying component.

    Accepts either a ``TrulyUnifiedCallbacks`` instance or a plain Dash app.
    Logs errors when the manager does not provide the necessary API.
    """
    if not _upload_component:
        logger.error("Upload component unavailable - skipping callback registration")
        return

    if not any(
        hasattr(manager, attr)
        for attr in ("register_callback", "unified_callback", "callback")
    ):
        logger.error("Unsupported callback manager: %s", type(manager))
        raise ValueError(f"Unsupported callback manager: {type(manager)}")

    callback_prefix = "file_upload"

    def _do_registration() -> None:
        if not hasattr(manager, "register_callback"):
            if hasattr(manager, "unified_callback"):
                manager.register_callback = manager.unified_callback  # type: ignore[attr-defined]
            elif hasattr(manager, "callback"):
                if TrulyUnifiedCallbacks:
                    wrapper = TrulyUnifiedCallbacks(manager)
                    manager.register_callback = wrapper.register_callback
                    manager.unified_callback = wrapper.unified_callback
                else:
                    manager.register_callback = manager.callback
                    manager.unified_callback = manager.callback
                    logger.warning(
                        "Using standard Dash callbacks - advanced features unavailable"
                    )
            else:
                raise ValueError(f"Unsupported callback manager: {type(manager)}")

        _upload_component.register_callbacks(manager, controller)

    _callback_registry.register_deduplicated(
        [
            f"{callback_prefix}_handle",
            f"{callback_prefix}_progress",
            f"{callback_prefix}_finalize",
        ],
        _do_registration,
        source_module="file_upload",
    )


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
    "safe_upload_layout",
    "register_upload_callbacks",
    "register_callbacks",
    "check_upload_system_health",
    "load_page",
]
