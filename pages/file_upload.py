#!/usr/bin/env python3
"""
File upload page - Fixed version without UI flash issues
"""
from __future__ import annotations

import base64
import io
import json
import logging
from typing import Any, Dict, List, Optional, Tuple

import dash_bootstrap_components as dbc
import pandas as pd
from dash import dcc, html

# Core imports that should always work
try:
    from core.callback_registry import _callback_registry
except ImportError:
    _callback_registry = None

try:
    from core.unicode import safe_encode_text, safe_decode_bytes
except ImportError:
    def safe_encode_text(text):
        return str(text)
    def safe_decode_bytes(data):
        return data.decode('utf-8', errors='replace')


from components.ui_component import UIComponent

logger = logging.getLogger(__name__)

# Global storage for uploaded files
_uploaded_files: Dict[str, pd.DataFrame] = {}


class UploadPage(UIComponent):
    """Upload page component."""

    def layout(self) -> dbc.Container:  # type: ignore[override]
        """Modern file upload layout with working drag-and-drop functionality."""

        return dbc.Container([
            # Header
            dbc.Row([
                dbc.Col([
                    html.H2("📁 File Upload", className="mb-3"),
                    html.P(
                        "Drag and drop files or click to browse. Supports CSV, Excel, and JSON files.",
                        className="text-muted mb-4",
                    ),
                ])
            ]),

            # Upload area
            dbc.Row([
                dbc.Col([
                    dcc.Upload(
                        id="drag-drop-upload",
                        children=html.Div(
                            [
                                html.I(
                                    className="fas fa-cloud-upload-alt fa-3x mb-3",
                                    style={"color": "#6c757d"},
                                ),
                                html.H5("Drag & Drop Files Here"),
                                html.P("or click to select files", className="text-muted"),
                                html.P(
                                    "Supports: .csv, .xlsx, .xls, .json",
                                    className="small text-muted",
                                ),
                            ],
                            style={
                                "textAlign": "center",
                                "padding": "60px",
                                "border": "2px dashed #dee2e6",
                                "borderRadius": "10px",
                                "cursor": "pointer",
                            },
                        ),
                        style={"width": "100%", "minHeight": "200px", "marginBottom": "20px"},
                        multiple=True,
                        accept=".csv,.xlsx,.xls,.json",
                        max_size=50 * 1024 * 1024,  # 50MB
                        className="upload-dropzone",
                    )
                ], lg=8, md=10, sm=12, className="mx-auto")
            ], className="mb-4"),

            # Upload status and progress
            dbc.Row([
                dbc.Col([
                    html.Div(id="upload-status", className="mb-3"),
                    dbc.Progress(
                        id="upload-progress",
                        value=0,
                        striped=True,
                        animated=False,
                        color="success",
                        style={"display": "none", "height": "8px"},
                        className="mb-3",
                    ),
                ], lg=8, md=10, sm=12, className="mx-auto")
            ]),

            # File preview area
            dbc.Row([
                dbc.Col([html.Div(id="preview-area")], lg=10, md=12, sm=12, className="mx-auto")
            ]),

            # Navigation area
            dbc.Row([
                dbc.Col([html.Div(id="upload-navigation")], lg=8, md=10, sm=12, className="mx-auto")
            ], className="mt-4"),

            # Data stores
            dcc.Store(id="uploaded-files-store", data={}),
            dcc.Store(id="upload-session-store", data={}),
        ], fluid=True, className="py-4")

    # ------------------------------------------------------------------
    def register_callbacks(self, manager, controller=None) -> None:  # type: ignore[override]
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
                                _uploaded_files[filename] = result["dataframe"]
                                updated_store[filename] = filename

                    if results:
                        preview = _create_file_preview(results)
                        status = _create_success_status(len(results))
                        progress_style = {"display": "block", "height": "8px"}

                        return preview, 100, progress_style, status, updated_store
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

            logger.info("✅ File upload callbacks registered successfully")

        except Exception as e:
            logger.error(f"❌ Failed to register file upload callbacks: {e}")


_upload_component = UploadPage()


def load_page(**kwargs) -> UploadPage:
    """Return a new :class:`UploadPage` instance."""

    return UploadPage(**kwargs)


def register_page() -> None:
    """Register the file upload page with Dash."""
    try:
        dash_register_page(__name__, path="/upload", name="Upload")
        logger.info("✅ File upload page registered")
    except Exception as e:
        logger.warning(f"Page registration failed: {e}")


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
        content_type, content_string = content.split(',')
        decoded = base64.b64decode(content_string)
        
        # Determine file type and read accordingly
        if filename.endswith('.csv'):
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        elif filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(decoded))
        elif filename.endswith('.json'):
            data = json.loads(decoded.decode('utf-8'))
            df = pd.json_normalize(data) if isinstance(data, list) else pd.DataFrame([data])
        else:
            logger.warning(f"Unsupported file type: {filename}")
            return None
        
        # Basic validation
        if df.empty:
            logger.warning(f"Empty file: {filename}")
            return None
        
        return {
            'filename': filename,
            'dataframe': df,
            'rows': len(df),
            'columns': len(df.columns),
            'size_mb': round(len(decoded) / (1024 * 1024), 2)
        }
        
    except Exception as e:
        logger.error(f"Error processing file {filename}: {e}")
        return None


def _create_file_preview(results: List[Dict[str, Any]]) -> List[Any]:
    """Create preview cards for uploaded files."""
    
    preview_cards = []
    
    for result in results:
        df = result['dataframe']
        filename = result['filename']
        
        # Create simple preview table (first 5 rows)
        preview_data = df.head(5).to_dict('records')
        columns = [{"name": col, "id": col} for col in df.columns]
        
        try:
            from dash import dash_table
            
            table = dash_table.DataTable(
                data=preview_data,
                columns=columns,
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'left', 'padding': '10px'},
                style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},
                page_size=5
            )
        except:
            # Fallback if dash_table not available
            table = html.P("Preview table not available")
        
        card = dbc.Card([
            dbc.CardHeader([
                html.H5(f"📁 {filename}", className="mb-0")
            ]),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.P(f"📊 {result['rows']:,} rows × {result['columns']} columns"),
                        html.P(f"💾 Size: {result['size_mb']} MB")
                    ], md=6),
                    dbc.Col([
                        html.P(f"📅 Uploaded: {pd.Timestamp.now().strftime('%H:%M:%S')}"),
                        html.P(f"✅ Status: Ready for analysis")
                    ], md=6)
                ]),
                
                html.Hr(),
                
                html.H6("Preview (first 5 rows):"),
                table
            ])
        ], className="mb-3")
        
        preview_cards.append(card)
    
    return preview_cards


def _create_success_status(file_count: int) -> Any:
    """Create success status message."""
    
    return dbc.Alert([
        html.H6(f"✅ Upload Successful!", className="mb-1"),
        html.P(f"Successfully processed {file_count} file(s). Ready for analysis.")
    ], color="success")


def _create_error_status(message: str) -> Any:
    """Create error status message."""
    
    return dbc.Alert([
        html.H6("❌ Upload Error", className="mb-1"),
        html.P(message)
    ], color="danger")


def _create_navigation_buttons(uploaded_files: Dict[str, str]) -> Any:
    """Create navigation buttons after successful upload."""
    
    return dbc.Card([
        dbc.CardBody([
            html.H6("🚀 Next Steps", className="mb-3"),
            dbc.ButtonGroup([
                dbc.Button(
                    [html.I(className="fas fa-chart-line me-2"), "Analyze Data"],
                    href="/analytics",
                    color="primary",
                    size="lg"
                ),
                dbc.Button(
                    [html.I(className="fas fa-upload me-2"), "Upload More"],
                    id="upload-more-btn",
                    color="secondary",
                    outline=True,
                    href="/upload"
                ),
                dbc.Button(
                    [html.I(className="fas fa-download me-2"), "Export"],
                    href="/export",
                    color="success",
                    outline=True
                )
            ], className="w-100")
        ])
    ], className="mt-3")


def safe_upload_layout():
    """Unicode-safe layout wrapper."""
    try:
        return layout()
    except Exception as e:
        logger.error(f"Upload layout failed: {e}")
        return _fallback_layout()



def clear_uploaded_data() -> None:
    """Clear uploaded data."""
    global _uploaded_files
    _uploaded_files.clear()


def get_uploaded_filenames() -> List[str]:
    """Get list of uploaded filenames."""
    return list(_uploaded_files.keys())


# Backward compatibility
def safe_upload_layout():
    """Compatibility function for app_factory."""
    return layout()


# Backward compatibility
register_upload_callbacks = register_callbacks

__all__ = [
    "UploadPage",
    "load_page",
    "layout",
    "safe_upload_layout",
    "register_page",
    "register_callbacks",
    "register_upload_callbacks",
    "get_uploaded_filenames",
    "get_uploaded_data",
    "clear_uploaded_data"
]
