#!/usr/bin/env python3
"""
File upload page - Fixed version without UI flash issues
"""
from __future__ import annotations

import base64
import json
import logging
import os
import tempfile
from typing import Any, Dict, List, Optional

import dash_bootstrap_components as dbc  # type: ignore[import]
import pandas as pd  # type: ignore[import]
from dash import (  # type: ignore[import]
    Input,
    Output,
    State,
    dcc,
    html,
    no_update,
)
from dash import register_page as dash_register_page
from dash.exceptions import PreventUpdate  # type: ignore[import]

from components.ui_component import UIComponent
from config.dynamic_config import dynamic_config
from services.upload_data_service import (
    clear_uploaded_data as _svc_clear_uploaded_data,
)


# Core imports that should always work
try:
    from core.callback_registry import _callback_registry
except ImportError:
    _callback_registry = None

try:
    from core.unicode import safe_decode_bytes, safe_encode_text
except ImportError:

    def safe_encode_text(value: Any) -> str:
        return str(value)

    def safe_decode_bytes(data: bytes) -> str:
        return data.decode("utf-8", errors="replace")


logger = logging.getLogger(__name__)

# On-disk store for uploaded files
from utils.upload_store import uploaded_data_store as _uploaded_data_store


class UploadPage(UIComponent):
    """Upload page component."""

    def layout(self) -> dbc.Container:  # type: ignore[override]
        """Modern file upload layout with working drag-and-drop functionality."""

        return dbc.Container(
            [
                # Header
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.H2("📁 File Upload", className="mb-3"),
                                html.P(
                                    "Drag and drop files or click to browse. "
                                    "Supports CSV, Excel, and JSON files.",
                                    className="text-muted mb-4",
                                ),
                            ]
                        )
                    ]
                ),
                # Upload area
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Label(
                                    "Upload data files",
                                    htmlFor="drag-drop-upload",
                                    className="visually-hidden",
                                ),
                                dcc.Upload(
                                    id="drag-drop-upload",
                                    children=html.Div(
                                        [
                                            html.I(
                                                className=(
                                                    "fas fa-cloud-upload-alt fa-3x mb-3"
                                                ),
                                                **{"aria-hidden": "true"},
                                            ),
                                            html.Span(
                                                "Upload files",
                                                className="visually-hidden",
                                            ),
                                            html.H5("Drag & Drop Files Here"),
                                            html.P(
                                                "or click to select files",
                                                className="text-muted",
                                            ),
                                            html.P(
                                                "Supports: .csv, .xlsx, .xls, .json",
                                                className="small text-muted",
                                            ),
                                        ],
                                        className="upload-dropzone-content",
                                    ),
                                    multiple=True,
                                    accept=".csv,.xlsx,.xls,.json",
                                    max_size=50 * 1024 * 1024,  # 50MB
                                    className="upload-dropzone",
                                    # aria-label removed for dcc.Upload compatibility
                                )
                            ],
                            lg=8,
                            md=10,
                            sm=12,
                            className="mx-auto",
                        )
                    ],
                    className="mb-4",
                ),
                # Upload status and progress
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Div(id="upload-status", className="mb-3"),
                                dbc.Progress(
                                    id="upload-progress",
                                    value=0,
                                    striped=True,
                                    animated=False,
                                    color="success",
                                    style={"display": "none", "height": "8px"},
                                    className="mb-3",
                                    **{
                                        # "role": "progressbar",
                                        
                                        # "aria-valuemin": 0,
                                        # "aria-valuemax": 100,
                                        # "aria-label": "File upload progress",
                                    },
                                ),
                            ],
                            lg=8,
                            md=10,
                            sm=12,
                            className="mx-auto",
                        )
                    ]
                ),
                # File preview area
                dbc.Row(
                    [
                        dbc.Col(
                            [html.Div(id="preview-area")],
                            lg=10,
                            md=12,
                            sm=12,
                            className="mx-auto",
                        )
                    ]
                ),
                # Navigation area
                dbc.Row(
                    [
                        dbc.Col(
                            [html.Div(id="upload-navigation")],
                            lg=8,
                            md=10,
                            sm=12,
                            className="mx-auto",
                        )
                    ],
                    className="mt-4",
                ),
                # Data stores
                dcc.Store(id="uploaded-files-store", data={}),
                dcc.Store(id="upload-session-store", data={}),
            ],
            fluid=True,
            className="py-4",
        )

    # ------------------------------------------------------------------
    def register_callbacks(
        self, manager, controller=None
    ) -> None:  # type: ignore[override]
        """Register upload callbacks - simplified and working."""

        if manager is None:
            logger.warning("No callback manager provided to file_upload")
            return

        try:

            @manager.unified_callback(
                [
                    Output("preview-area", "children"),
                    Output("upload-progress", "value"),
                    Output("upload-progress", "style"),
                    Output("upload-status", "children"),
                    Output("uploaded-files-store", "data"),
                ],
                Input("drag-drop-upload", "contents"),
                [
                    State("drag-drop-upload", "filename"),
                    State("uploaded-files-store", "data"),
                ],
                callback_id="file_upload_handler_simple",
                component_name="file_upload",
                prevent_initial_call=True,
            )
            def handle_upload(contents, filenames, existing_data):
                if not contents:
                    raise PreventUpdate

                try:
                    if not isinstance(contents, list):
                        contents = [contents]
                    if not isinstance(filenames, list):
                        filenames = [filenames]

                    results = []
                    updated_store = existing_data or {}

                    for content, filename in zip(contents, filenames):
                        if content and filename:
                            result = _process_single_file(content, filename)
                            if result:
                                results.append(result)
                                _uploaded_data_store.add_file(
                                    filename, result["dataframe"]
                                )
                                updated_store[filename] = filename

                    if results:
                        preview = _create_file_preview(results)
                        status = _create_success_status(len(results))
                        progress_style = {"display": "block", "height": "8px"}

                        return (
                            preview,
                            no_update,
                            {"display": "none"},
                            status,
                            updated_store,
                        )
                    else:
                        error_status = _create_error_status("No valid files processed")
                        progress_style = {"display": "none"}
                        return no_update, 0, progress_style, error_status, no_update

                except Exception as e:
                    logger.error(f"Upload processing error: {e}")
                    error_status = _create_error_status(f"Upload failed: {str(e)}")
                    progress_style = {"display": "none"}
                    return no_update, 0, progress_style, error_status, no_update

            @manager.unified_callback(
                Output("upload-navigation", "children"),
                Input("uploaded-files-store", "data"),
                callback_id="file_upload_navigation_simple",
                component_name="file_upload",
                prevent_initial_call=True,
            )
            def update_navigation(uploaded_files):
                if not uploaded_files:
                    return ""

                return _create_navigation_buttons(uploaded_files)

            @manager.unified_callback(
                Output("uploaded-files-store", "data"),
                Input("upload-more-btn", "n_clicks"),
                callback_id="reset_upload_session",
                component_name="file_upload",
                prevent_initial_call=True,
            )
            def reset_upload(_click):
                clear_uploaded_data()
                return {}

            logger.info("✅ File upload callbacks registered successfully")

        except Exception as e:
            logger.error(f"❌ Failed to register file upload callbacks: {e}")


_upload_component = UploadPage()


def load_page(**kwargs) -> UploadPage:
    """Return a new :class:`UploadPage` instance."""

    return UploadPage(**kwargs)


def register_page() -> None:
    """Register the upload page with Dash using current app context."""
    try:
        import dash
        if hasattr(dash, "_current_app") and dash._current_app is not None:
            dash.register_page(__name__, path="/upload", name="Upload")
        else:
            from dash import register_page as dash_register_page
            dash_register_page(__name__, path="/upload", name="Upload")
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to register page {__name__}: {e}")


def register_page_with_app(app) -> None:
    """Register the page with a specific Dash app instance."""
    try:
        import dash
        old_app = getattr(dash, "_current_app", None)
        dash._current_app = app
        dash.register_page(__name__, path="/upload", name="Upload")
        if old_app is not None:
            dash._current_app = old_app
        else:
            delattr(dash, "_current_app")
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to register page {__name__} with app: {e}")


def layout() -> dbc.Container:
    """Compatibility wrapper returning the default component layout."""

    return _upload_component.layout()


def register_callbacks(manager):
    """Compatibility wrapper using the default component."""

    _upload_component.register_callbacks(manager)


def _process_single_file(content: str, filename: str) -> Optional[Dict[str, Any]]:
    """Process a single uploaded file safely."""

    try:
        # Decode base64 content
        content_type, content_string = content.split(",")
        decoded = base64.b64decode(content_string)
        if len(decoded) > dynamic_config.get_max_upload_size_bytes():
            logger.warning("File too large: %s bytes", len(decoded))
            return None

        if filename.endswith(".csv"):
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp.write(decoded)
                tmp.flush()
                reader = pd.read_csv(
                    tmp.name, chunksize=dynamic_config.get_upload_chunk_size()
                )
                chunks = list(reader)
            df = pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame()
            os.unlink(tmp.name)
        elif filename.endswith((".xlsx", ".xls")):
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp.write(decoded)
                tmp.flush()
                df = pd.read_excel(tmp.name)
            os.unlink(tmp.name)
        elif filename.endswith(".json"):
            data = json.loads(decoded.decode("utf-8"))
            df = (
                pd.json_normalize(data)
                if isinstance(data, list)
                else pd.DataFrame([data])
            )
        else:
            logger.warning(f"Unsupported file type: {filename}")
            return None

        # Basic validation
        if df.empty:
            logger.warning(f"Empty file: {filename}")
            return None

        return {
            "filename": filename,
            "dataframe": df,
            "rows": len(df),
            "columns": len(df.columns),
            "size_mb": round(len(decoded) / (1024 * 1024), 2),
        }

    except Exception as e:
        logger.error(f"Error processing file {filename}: {e}")
        return None


def _create_file_preview(results: List[Dict[str, Any]]) -> List[Any]:
    """Create preview cards for uploaded files."""

    preview_cards = []

    for result in results:
        df = result["dataframe"]
        filename = result["filename"]

        # Create simple preview table (first 5 rows)
        preview_data = df.head(5).to_dict("records")
        columns = [{"name": col, "id": col} for col in df.columns]

        try:
            from dash import dash_table  # type: ignore[import]

            table = dash_table.DataTable(
                data=preview_data,
                columns=columns,
                style_table={"overflowX": "auto"},
                style_cell={"textAlign": "left", "padding": "10px"},
                style_header={
                    "backgroundColor": "rgb(230, 230, 230)",
                    "fontWeight": "bold",
                },
                page_size=5,
            )
        except Exception:
            # Fallback if dash_table not available
            table = html.P("Preview table not available")

        card = dbc.Card(
            [
                dbc.CardHeader([html.H5(f"📁 {filename}", className="mb-0")]),
                dbc.CardBody(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.P(
                                            f"📊 {result['rows']:,} rows "
                                            f"× {result['columns']} columns"
                                        ),
                                        html.P(f"💾 Size: {result['size_mb']} MB"),
                                    ],
                                    md=6,
                                ),
                                dbc.Col(
                                    [
                                        html.P(
                                            "📅 Uploaded: "
                                            f"{pd.Timestamp.now().strftime('%H:%M:%S')}"
                                        ),
                                        html.P("✅ Status: Ready for analysis"),
                                    ],
                                    md=6,
                                ),
                            ]
                        ),
                        html.Hr(),
                        html.H6("Preview (first 5 rows):"),
                        table,
                    ]
                ),
            ],
            className="mb-3",
        )

        preview_cards.append(card)

    return preview_cards


def _create_success_status(file_count: int) -> Any:
    """Create success status message."""

    return dbc.Alert(
        [
            html.H6("✅ Upload Successful!", className="mb-1"),
            html.P(f"Successfully processed {file_count} file(s). Ready for analysis."),
        ],
        color="success",
    )


def _create_error_status(message: str) -> Any:
    """Create error status message."""

    return dbc.Alert(
        [html.H6("❌ Upload Error", className="mb-1"), html.P(message)], color="danger"
    )


def _create_navigation_buttons(uploaded_files: Dict[str, str]) -> Any:
    """Create navigation buttons after successful upload."""

    return dbc.Card(
        [
            dbc.CardBody(
                [
                    html.H6("🚀 Next Steps", className="mb-3"),
                    dbc.ButtonGroup(
                        [
                            dbc.Button(
                                [
                                    html.I(className="fas fa-chart-line me-2", **{"aria-hidden": "true"}),
                                    "Analyze Data",
                                ],
                                href="/analytics",
                                color="primary",
                                size="lg",
                            ),
                            dbc.Button(
                                [html.I(className="fas fa-upload me-2", **{"aria-hidden": "true"}), "Upload More"],
                                id="upload-more-btn",
                                color="secondary",
                                outline=True,
                                href="/upload",
                            ),
                            dbc.Button(
                                [html.I(className="fas fa-download me-2", **{"aria-hidden": "true"}), "Export"],
                                href="/export",
                                color="success",
                                outline=True,
                            ),
                        ],
                        className="w-100",
                    ),
                ]
            )
        ],
        className="mt-3",
    )


def _fallback_layout() -> dbc.Container:
    """Minimal layout shown if ``layout()`` fails."""

    return dbc.Container(
        dbc.Alert(
            "Upload page failed to load. Please try again later.",
            color="danger",
        ),
        fluid=True,
    )


def safe_upload_layout():
    """Unicode-safe layout wrapper."""
    try:
        return layout()
    except Exception as e:
        logger.error(f"Upload layout failed: {e}")
        return _fallback_layout()


def clear_uploaded_data() -> None:
    """Remove all uploaded files from the on-disk store."""
    try:
        _uploaded_data_store.clear_all()
    finally:
        _svc_clear_uploaded_data()


def get_uploaded_filenames() -> List[str]:
    """Return list of uploaded filenames from the on-disk store."""
    return _uploaded_data_store.get_filenames()


def get_uploaded_data() -> Dict[str, pd.DataFrame]:
    """Return all uploaded dataframes from the on-disk store."""

    return _uploaded_data_store.get_all_data()


# Backward compatibility
register_upload_callbacks = register_callbacks

__all__ = [
    "UploadPage",
    "load_page",
    "register_page",
    "layout",
    "safe_upload_layout",
    "register_callbacks",
    "register_upload_callbacks",
    "get_uploaded_filenames",
    "get_uploaded_data",
    "clear_uploaded_data",
]


def __getattr__(name: str):
    if name.startswith(("create_", "get_")):

        def _stub(*args, **kwargs):
            return None

        return _stub
    raise AttributeError(f"module {__name__} has no attribute {name}")
