"""File upload page wired to the unified upload component."""

import dash
import dash_bootstrap_components as dbc

from core.callback_registry import _callback_registry

html = dash.html

_upload_component = None

# Import your existing upload component function
try:
    from components import create_upload_card  # Use existing function

    HAS_UPLOAD_COMPONENT = True
except ImportError:
    HAS_UPLOAD_COMPONENT = False


def layout():
    if HAS_UPLOAD_COMPONENT:
        return dbc.Container(
            [
                html.H2("File Upload"),
                create_upload_card(),  # Use existing upload component
            ]
        )
    else:
        return dbc.Container(
            [html.H2("File Upload"), html.P("Upload component not available")]
        )


def safe_upload_layout():
    return layout()


def register_callbacks(manager):
    """Register upload callbacks with the provided manager."""

    global _upload_component

    try:
        from components.upload import UnifiedUploadComponent
        from services.upload.controllers.upload_controller import (
            UnifiedUploadController,
        )
    except Exception as exc:  # pragma: no cover - optional imports
        import logging

        logging.getLogger(__name__).error("Failed to import upload modules: %s", exc)
        return

    _upload_component = UnifiedUploadComponent()
    controller = UnifiedUploadController(callbacks=manager)

    callback_defs = (
        controller.upload_callbacks()
        + controller.progress_callbacks()
        + controller.validation_callbacks()
    )

    callback_ids = [cid for _, _, _, _, cid, _ in callback_defs]

    def _do_registration() -> None:
        for func, outputs, inputs, states, cid, extra in callback_defs:
            manager.unified_callback(
                outputs,
                inputs,
                states,
                callback_id=cid,
                component_name="file_upload",
                **extra,
            )(func)

    _callback_registry.register_deduplicated(
        callback_ids, _do_registration, source_module="file_upload"
    )


def get_uploaded_filenames(service=None, container=None):
    from services.upload_data_service import get_uploaded_filenames as _get

    return _get(service=service, container=container)


def register_page():
    from dash import register_page as dash_register_page

    dash_register_page(__name__, path="/upload", name="Upload")


register_upload_callbacks = register_callbacks


__all__ = [
    "layout",
    "safe_upload_layout",
    "register_page",
    "register_callbacks",
    "register_upload_callbacks",
    "get_uploaded_filenames",
]
