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


logger = logging.getLogger(__name__)

# Global storage for uploaded files
_uploaded_files: Dict[str, pd.DataFrame] = {}


def register_page() -> None:
    """Register the file upload page with Dash."""
    try:
        dash_register_page(__name__, path="/upload", name="Upload")
        logger.info("✅ File upload page registered")
    except Exception as e:
        logger.warning(f"Page registration failed: {e}")


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


    if manager is None:
        logger.warning("No callback manager provided to file_upload")
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
        def handle_upload(contents, filenames, existing_data):
            """Handle file uploads with proper error handling."""
            
            if not contents:
                raise PreventUpdate
            
            try:
                # Ensure inputs are lists
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
                            # Store in global and component store
                            _uploaded_files[filename] = result['dataframe']
                            updated_store[filename] = filename
                
                if results:
                    preview = _create_file_preview(results)
                    status = _create_success_status(len(results))
                    progress_style = {'display': 'block', 'height': '8px'}
                    
                    return preview, 100, progress_style, status, updated_store
                else:
                    error_status = _create_error_status("No valid files processed")
                    progress_style = {'display': 'none'}
                    return no_update, 0, progress_style, error_status, no_update
                    
            except Exception as e:
                logger.error(f"Upload processing error: {e}")
                error_status = _create_error_status(f"Upload failed: {str(e)}")
                progress_style = {'display': 'none'}
                return no_update, 0, progress_style, error_status, no_update

        @manager.unified_callback(
            Output("upload-navigation", "children"),
            Input("uploaded-files-store", "data"),
            callback_id="file_upload_navigation_simple",
            component_name="file_upload",
            prevent_initial_call=True
        )
        def update_navigation(uploaded_files):
            """Update navigation options after successful upload."""
            
            if not uploaded_files:
                return ""
            
            return _create_navigation_buttons(uploaded_files)

        logger.info("✅ File upload callbacks registered successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to register file upload callbacks: {e}")


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
    "layout",
    "safe_upload_layout", 
    "register_page",
    "register_callbacks",
    "register_upload_callbacks",
    "get_uploaded_filenames",
    "get_uploaded_data",
    "clear_uploaded_data"
]
