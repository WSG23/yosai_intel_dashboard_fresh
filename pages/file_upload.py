#!/usr/bin/env python3
"""
File upload page - Modern implementation with working drag-and-drop.
Maintains backward compatibility while adding robust upload functionality.
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

logger = logging.getLogger(__name__)



# Try to import advanced services - graceful fallback
try:
    from services.upload.controllers.upload_controller import UnifiedUploadController
    CONTROLLER_AVAILABLE = True
    logger.info("✅ Upload controller available")
except ImportError:
    CONTROLLER_AVAILABLE = False
    logger.info("ℹ️ No upload controller - using basic functionality")


def layout():
    """Return the standard upload layout or a minimal fallback."""

    try:
        from components.upload import UnifiedUploadComponent
        return UnifiedUploadComponent().layout()
    except Exception as exc:  # pragma: no cover - fallback for missing deps
        logger.error("Failed to create UnifiedUploadComponent layout: %s", exc)
        return _fallback_layout()


def _fallback_layout() -> html.Div:
    """Provide a minimal layout with the IDs expected by callbacks."""
    return dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(
                        dcc.Upload(id="drag-drop-upload", children=html.Div("Upload Files"), multiple=True)
                    )
                ]
            ),
            dbc.Row([
                dbc.Col(dbc.Progress(id="upload-progress", value=0, label="0%", striped=True, animated=True))
            ], className="mb-2"),
            dbc.Row([
                dbc.Col(html.Ul(id="file-progress-list", className="list-unstyled"))
            ]),
            dbc.Button("", id="progress-done-trigger", className="visually-hidden"),
            html.Div(id="preview-area"),
            dbc.Button("Next", id="to-column-map-btn", color="primary", className="mt-2", disabled=True),
            dcc.Store(id="uploaded-df-store"),
            dcc.Store(id="file-info-store", data={}),
            dcc.Store(id="current-file-info-store"),
            dcc.Store(id="current-session-id"),
            dcc.Store(id="upload-task-id"),
            dcc.Store(id="client-validation-store", data=[]),
            dcc.Interval(id="upload-progress-interval", interval=1000, disabled=True),
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle("Column Mapping")),
                    dbc.ModalBody("", id="modal-body"),
                    dbc.ModalFooter([
                        dbc.Button("Cancel", id="column-verify-cancel", color="secondary"),
                        dbc.Button("Confirm", id="column-verify-confirm", color="success"),
                    ]),
                ],
                id="column-verification-modal",
                is_open=False,
                size="xl",
            ),
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle("Device Classification")),
                    dbc.ModalBody("", id="device-modal-body"),
                    dbc.ModalFooter([
                        dbc.Button("Cancel", id="device-verify-cancel", color="secondary"),
                        dbc.Button("Confirm", id="device-verify-confirm", color="success"),
                    ]),
                ],
                id="device-verification-modal",
                is_open=False,
                size="xl",
            ),
        ],
        fluid=True,
    )


def register_callbacks(manager):
    """Register upload callbacks with the provided manager."""

    global _upload_component

    try:
        from components.upload import UnifiedUploadComponent
    except Exception as exc:
        import logging
        logging.getLogger(__name__).error("Failed to import upload modules: %s", exc)
        return

    _upload_component = UnifiedUploadComponent()
    
    if not manager:
        raise RuntimeError("Callback manager is required")

    def _do_registration() -> None:
        _upload_component.register_callbacks(manager)

    callback_ids = [
        "file_upload_handle",
        "file_upload_progress",
        "file_upload_finalize",
    ]

    _callback_registry.register_deduplicated(
        callback_ids, _do_registration, source_module=__name__

    )
    def handle_modern_upload(contents, filenames, last_modified, file_store):
        """Process uploaded files and update UI components."""
        if not contents:
            raise PreventUpdate

        if not isinstance(contents, list):
            contents = [contents]
            filenames = [filenames]

        file_store = file_store or {}
        previews = []
        status_alerts = []

        for content, fname in zip(contents, filenames):
            df, err = _process_upload_safe(content, fname)
            if df is None:
                status_alerts.append(
                    dbc.Alert(f"❌ {fname}: {err}", color="danger", dismissable=True)
                )
                continue

            previews.append(_create_modern_preview(df, fname))
            file_store[fname] = {"rows": len(df), "columns": len(df.columns)}
            status_alerts.append(
                dbc.Alert(f"✅ Uploaded {fname}", color="success", dismissable=True)
            )

        progress = 100 if previews else 0
        progress_style = {"display": "block"} if previews else {"display": "none"}
        navigation = (
            _create_navigation_section(len(file_store), file_store)
            if previews
            else no_update
        )

        return (
            status_alerts,
            progress,
            progress_style,
            previews,
            file_store,
            navigation,
        )



def _process_upload_safe(contents, filename):
    """Safely process uploaded file with comprehensive error handling."""
    try:
        if not contents or not filename:
            return None, "No file content provided"
        
        # Decode file content
        try:
            content_type, content_string = contents.split(',', 1)
            decoded_bytes = base64.b64decode(content_string)
        except Exception as e:
            return None, f"Failed to decode file content: {str(e)}"
        
        # Safe filename processing
        try:
            filename = safe_encode_text(filename)
        except Exception:
            filename = str(filename)  # Fallback
        
        # Process by file type
        file_ext = filename.lower().split('.')[-1]
        
        try:
            if file_ext == 'json':
                decoded_text = safe_decode_bytes(decoded_bytes)
                data = json.loads(decoded_text)
                df = pd.DataFrame(data)
                
            elif file_ext in ['csv', 'txt']:
                decoded_text = safe_decode_bytes(decoded_bytes)
                # Try different encodings if needed
                try:
                    df = pd.read_csv(io.StringIO(decoded_text))
                except UnicodeDecodeError:
                    decoded_text = decoded_bytes.decode('latin1')
                    df = pd.read_csv(io.StringIO(decoded_text))
                    
            elif file_ext in ['xlsx', 'xls']:
                df = pd.read_excel(io.BytesIO(decoded_bytes))
                
            else:
                return None, f"Unsupported file type: .{file_ext}"
        
        except Exception as e:
            return None, f"Failed to parse {file_ext.upper()} file: {str(e)}"
        
        # Validate DataFrame
        if df.empty:
            return None, "File appears to be empty"
        
        # Clean column names
        df.columns = df.columns.astype(str)
        
        return df, ""
        
    except Exception as e:
        logger.error(f"Upload processing error for {filename}: {str(e)}")
        return None, f"Processing failed: {str(e)}"


def _create_modern_preview(df, filename):
    """Create a modern, responsive preview component."""
    try:
        from dash import dash_table
        
        # Analyze data types
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        text_cols = df.select_dtypes(include=['object']).columns.tolist()
        datetime_cols = df.select_dtypes(include=['datetime']).columns.tolist()
        
        # Create preview data (first 10 rows)
        preview_data = df.head(10).fillna('').to_dict('records')
        
        # Modern data table
        data_table = dash_table.DataTable(
            data=preview_data,
            columns=[{
                'name': col,
                'id': col,
                'type': 'numeric' if col in numeric_cols else 'text'
            } for col in df.columns],
            
            # Styling
            style_table={
                'overflowX': 'auto',
                'maxHeight': '400px',
                'border': '1px solid #dee2e6',
                'borderRadius': '8px'
            },
            style_header={
                'backgroundColor': '#f8f9fa',
                'fontWeight': 'bold',
                'textAlign': 'center',
                'border': '1px solid #dee2e6',
                'fontSize': '14px'
            },
            style_cell={
                'textAlign': 'left',
                'padding': '12px',
                'fontSize': '13px',
                'fontFamily': 'system-ui, -apple-system, sans-serif',
                'border': '1px solid #dee2e6'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': '#f8f9fa'
                }
            ],
            
            # Features
            page_size=10,
            sort_action='native',
            filter_action='native' if len(df) > 50 else 'none'
        )
        
        return dbc.Card([
            dbc.CardHeader([
                dbc.Row([
                    dbc.Col([
                        html.H5([
                            html.I(className="fas fa-table me-2"),
                            filename
                        ], className="mb-0")
                    ], width=8),
                    dbc.Col([
                        dbc.Badge(f"{len(df):,} rows", color="primary", className="me-2"),
                        dbc.Badge(f"{len(df.columns)} cols", color="info")
                    ], width=4, className="text-end")
                ])
            ]),
            dbc.CardBody([
                # Data type summary
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            dbc.Badge(f"🔢 {len(numeric_cols)} numeric", color="success", className="me-2"),
                            dbc.Badge(f"📝 {len(text_cols)} text", color="warning", className="me-2"),
                            dbc.Badge(f"📅 {len(datetime_cols)} dates", color="info", className="me-2"),
                        ])
                    ])
                ], className="mb-3"),
                
                # Data table
                data_table,
                
                # Column listing for large datasets
                html.Details([
                    html.Summary("View all columns", className="text-muted small"),
                    html.Div([
                        dbc.Badge(col, color="light", text_color="dark", className="me-1 mb-1")
                        for col in df.columns
                    ], className="mt-2")
                ], className="mt-3") if len(df.columns) > 10 else None
            ])
        ], className="mb-4")
        
    except Exception as e:
        logger.error(f"Preview creation failed: {str(e)}")
        # Fallback preview
        return dbc.Alert([
            html.H5(f"✅ Uploaded: {filename}"),
            html.P(f"📊 {len(df)} rows × {len(df.columns)} columns")
        ], color="light", className="mb-3")


def _create_navigation_section(successful_count, file_store):
    """Create navigation section after successful uploads."""
    return dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.H4([
                        html.I(className="fas fa-rocket me-2"),
                        "Ready for Analysis!"
                    ], className="text-success mb-3"),
                    html.P([
                        f"Successfully uploaded ",
                        html.Strong(f"{successful_count} file(s)"),
                        f" with ",
                        html.Strong(f"{sum(f.get('rows', 0) for f in file_store.values()):,} total rows")
                    ], className="mb-4")
                ], width=12)
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.ButtonGroup([
                        dbc.Button([
                            html.I(className="fas fa-chart-line me-2"),
                            "Start Analysis"
                        ], href="/analytics", color="success", size="lg"),
                        dbc.Button([
                            html.I(className="fas fa-plus me-2"),
                            "Upload More"
                        ], id="upload-more-files", color="outline-primary", size="lg"),
                    ], className="d-flex gap-2 justify-content-center")
                ])
            ])
        ])
    ], color="light", className="border-success")


def safe_upload_layout():
    """Unicode-safe layout wrapper."""
    try:
        return layout()
    except Exception as e:
        logger.error(f"Upload layout failed: {e}")
        return _fallback_layout()


def get_uploaded_filenames(service=None, container=None):
    """Get uploaded filenames - compatibility function."""
    try:
        from services.upload_data_service import get_uploaded_filenames as _get
        return _get(service=service, container=container)
    except ImportError:
        logger.warning("Upload data service not available")
        return []


def register_page():
    """Register the file upload page with Dash."""
    try:
        from dash import register_page as dash_register_page
        dash_register_page(__name__, path="/upload", name="Upload")
    except Exception as e:
        logger.warning(f"Page registration failed: {e}")


# Backward compatibility
register_upload_callbacks = register_callbacks

__all__ = [
    "layout",
    "safe_upload_layout",
    "register_page", 
    "register_callbacks",
    "register_upload_callbacks",
    "get_uploaded_filenames",
]

import importlib

_component_available = False
try:
    spec = importlib.util.find_spec("components")
    if spec:
        module = importlib.import_module("components")
        _component_available = hasattr(module, "create_upload_card")
except Exception:
    _component_available = False

logger.info(
    "🚀 File upload loaded - Controller: %s, Upload component available: %s",
    CONTROLLER_AVAILABLE,
    _component_available,
)
