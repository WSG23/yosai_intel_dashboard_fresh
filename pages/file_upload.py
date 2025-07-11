"""File upload page wired to the unified upload component."""

import dash
import dash_bootstrap_components as dbc
from dash import dash_table, Input, Output, State
import pandas as pd
import base64
import io
import json
from dash.exceptions import PreventUpdate
from core.unicode import safe_encode_text, safe_decode_bytes

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
    """Register upload callbacks using the unified system."""

    @manager.unified_callback(
        [
            Output("preview-area", "children"),
            Output("upload-progress", "value"),
            Output("upload-progress", "label"),
            Output("to-column-map-btn", "disabled"),
            Output("uploaded-df-store", "data"),
        ],
        [Input("drag-drop-upload", "contents"), State("drag-drop-upload", "filename")],
        callback_id="file_upload_handle",
        component_name="file_upload",
        prevent_initial_call=True,
    )
    def handle_upload(contents, filenames):
        if not contents or not filenames:
            raise PreventUpdate

        if not isinstance(contents, list):
            contents = [contents]
            filenames = [filenames]

        previews = []
        stored: dict[str, str] = {}

        for content, fname in zip(contents, filenames):
            try:
                _, data = content.split(",", 1)
                decoded = base64.b64decode(data)
                text = safe_decode_bytes(decoded)
                if str(fname).lower().endswith(".json"):
                    df = pd.DataFrame(json.loads(text))
                else:
                    df = pd.read_csv(io.StringIO(text))
            except Exception as exc:  # pragma: no cover - show error to user
                alert = dbc.Alert(
                    f"Failed to process {safe_encode_text(fname)}: {exc}", color="danger"
                )
                return alert, 0, "0%", True, {}

            stored[str(fname)] = df.to_json(date_format="iso", orient="split")
            if not previews:
                previews.append(
                    dash_table.DataTable(
                        data=df.head().to_dict("records"),
                        columns=[{"name": c, "id": c} for c in df.columns],
                        page_size=5,
                    )
                )

        preview_layout = previews[0] if previews else html.Div()
        return preview_layout, 100, "100%", False, stored


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
