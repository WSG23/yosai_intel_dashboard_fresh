"""File upload page wired to the unified upload component."""

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output
import logging

logger = logging.getLogger(__name__)

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
    """Register upload callbacks using unified system."""

    @manager.unified_callback(
        [Output('preview-area', 'children'),
         Output('upload-progress', 'value')],
        Input('drag-drop-upload', 'contents'),
        callback_id="file_upload_handler",
        component_name="file_upload",
        prevent_initial_call=True
    )
    def handle_upload(contents):
        from core.unicode import safe_encode_text, safe_decode_bytes

        if not contents:
            return [], 0

        # Your existing upload logic with Unicode safety
        try:
            # Process upload safely
            filename = safe_encode_text("uploaded_file.csv")
            # Add your processing logic here
            return [f"Uploaded: {filename}"], 100
        except Exception as e:
            logger.error(f"Upload error: {e}")
            return [f"Error: {str(e)}"], 0


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
