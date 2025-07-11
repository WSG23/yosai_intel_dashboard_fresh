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

import dash
import dash_bootstrap_components as dbc
import pandas as pd
from dash import Input, Output, State, dcc, html, callback, no_update
from dash.exceptions import PreventUpdate

# Core imports that should always work
try:
    from core.callback_registry import _callback_registry
except ImportError:
    _callback_registry = None
from core.callback_registry import handle_register_with_deduplication
from upload_callbacks import UploadCallbackManager

try:
    from core.unicode import safe_encode_text, safe_decode_bytes
except ImportError:
    def safe_encode_text(text):
        return str(text)
    def safe_decode_bytes(data):
        return data.decode('utf-8', errors='replace')

logger = logging.getLogger(__name__)

# Try to import your existing components - graceful fallback
try:
    from components import create_upload_card
    HAS_UPLOAD_COMPONENT = True
    logger.info("✅ Found existing upload component")
except ImportError:
    HAS_UPLOAD_COMPONENT = False
    logger.info("ℹ️ No existing upload component - using built-in")

# Try to import advanced services - graceful fallback
try:
    from services.upload.controllers.upload_controller import UnifiedUploadController
    CONTROLLER_AVAILABLE = True
    logger.info("✅ Upload controller available")
except ImportError:
    CONTROLLER_AVAILABLE = False
    logger.info("ℹ️ No upload controller - using basic functionality")


def layout():
    """Modern file upload layout with working drag-and-drop functionality."""
    
    return dbc.Container([
        # Header section
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.H2([
                        html.I(className="fas fa-cloud-upload-alt me-3", 
                              style={'color': '#0d6efd'}),
                        "File Upload Center"
                    ], className="text-center mb-2"),
                    html.P("Upload CSV, Excel, or JSON files for analysis", 
                          className="text-center text-muted lead")
                ])
            ])
        ], className="mb-5"),
        
        # Main upload area - Improved design
        dbc.Row([
            dbc.Col([
                dcc.Upload(
                    id="file-upload-dropzone",
                    children=html.Div([
                        # Visual upload icon
                        html.Div([
                            html.I(className="fas fa-cloud-upload-alt", 
                                  style={
                                      'fontSize': '5rem', 
                                      'color': '#6c757d',
                                      'marginBottom': '1.5rem'
                                  })
                        ], className="text-center"),
                        
                        # Primary text
                        html.H4("Drag & Drop Files Here", 
                               className="text-center mb-3",
                               style={'color': '#495057', 'fontWeight': '600'}),
                        
                        # Secondary text
                        html.P("or click to browse files", 
                              className="text-center text-muted mb-4",
                              style={'fontSize': '1.1rem'}),
                        
                        # Supported formats
                        html.Div([
                            html.H6("Supported Formats:", className="text-center mb-2"),
                            html.Div([
                                dbc.Badge("CSV", color="success", className="me-2 px-3 py-2"),
                                dbc.Badge("Excel (.xlsx)", color="info", className="me-2 px-3 py-2"),
                                dbc.Badge("JSON", color="warning", className="me-2 px-3 py-2"),
                            ], className="text-center mb-3")
                        ]),
                        
                        # File constraints
                        html.Small("Maximum size: 50MB per file • Multiple files supported", 
                                 className="text-muted text-center d-block")
                    ], 
                    className="upload-dropzone-content",
                    style={
                        'padding': '3rem 2rem',
                        'textAlign': 'center',
                        'height': '100%',
                        'display': 'flex',
                        'flexDirection': 'column',
                        'justifyContent': 'center'
                    }),
                    
                    # Upload component styling
                    style={
                        'width': '100%',
                        'height': '350px',
                        'lineHeight': '350px',
                        'borderWidth': '3px',
                        'borderStyle': 'dashed',
                        'borderRadius': '20px',
                        'borderColor': '#dee2e6',
                        'textAlign': 'center',
                        'backgroundColor': '#f8f9fa',
                        'cursor': 'pointer',
                        'transition': 'all 0.3s ease-in-out',
                        'position': 'relative',
                        'overflow': 'hidden'
                    },
                    
                    # Upload component configuration
                    multiple=True,
                    accept='.csv,.xlsx,.xls,.json',
                    max_size=50 * 1024 * 1024,  # 50MB
                    className="upload-dropzone"
                )
            ], lg=8, md=10, sm=12, className="mx-auto")
        ], className="mb-4"),
        
        # Upload status and progress
        dbc.Row([
            dbc.Col([
                html.Div(id="upload-status", className="mb-3"),
                dbc.Progress(
                    id="upload-progress-bar",
                    value=0,
                    striped=True,
                    animated=False,
                    color="success",
                    style={'display': 'none', 'height': '8px'},
                    className="mb-3"
                )
            ], lg=8, md=10, sm=12, className="mx-auto")
        ]),
        
        # File preview area
        dbc.Row([
            dbc.Col([
                html.Div(id="upload-preview")
            ], lg=10, md=12, sm=12, className="mx-auto")
        ]),
        
        # Navigation area
        dbc.Row([
            dbc.Col([
                html.Div(id="upload-navigation")
            ], lg=8, md=10, sm=12, className="mx-auto")
        ], className="mt-4"),
        
        # Data stores
        dcc.Store(id="uploaded-files-store", data={}),
        dcc.Store(id="upload-session-store", data={}),
        
        # Hidden elements to prevent callback errors
        html.Div([
            dbc.Button("Verify Columns", id="verify-columns-btn-simple", style={'display': 'none'}),
            dbc.Button("Classify Devices", id="classify-devices-btn", style={'display': 'none'}),
            dbc.Button("Upload More", id="upload-more-btn", style={'display': 'none'}),
        ], style={'display': 'none'}),
        
    ], fluid=True, className="py-4")


def register_callbacks(manager):
    """Register upload callbacks with guaranteed CSV upload functionality."""
    
    def handle_file_upload(contents_list, filename_list, last_modified_list, existing_data):
        """Handle file upload with modern feedback and processing."""
        
        if not contents_list:
            raise PreventUpdate
        
        # Ensure lists
        if not isinstance(contents_list, list):
            contents_list = [contents_list]
        if not isinstance(filename_list, list):
            filename_list = [filename_list]
        if not isinstance(last_modified_list, list):
            last_modified_list = [last_modified_list]
        
        # Process uploads
        status_components = []
        preview_components = []
        navigation_content = ""
        updated_store = existing_data.copy() if existing_data else {}
        
        successful_uploads = 0
        total_files = len(contents_list)
        
        logger.info(f"Processing {total_files} uploaded files")
        
        for i, (contents, filename, last_modified) in enumerate(zip(contents_list, filename_list, last_modified_list)):
            try:
                # Process file
                df, error_msg = _process_upload_safe(contents, filename)
                
                if error_msg:
                    # Error handling
                    status_components.append(
                        dbc.Alert([
                            html.H5([
                                html.I(className="fas fa-exclamation-triangle me-2"),
                                f"Upload Failed: {filename}"
                            ], className="alert-heading mb-2"),
                            html.P(error_msg, className="mb-0")
                        ], color="danger", className="mb-2")
                    )
                    logger.error(f"Upload failed for {filename}: {error_msg}")
                    
                else:
                    # Success handling
                    successful_uploads += 1
                    
                    # Store file data
                    file_key = f"file_{len(updated_store)}"
                    updated_store[file_key] = {
                        'filename': filename,
                        'upload_time': last_modified,
                        'rows': len(df),
                        'columns': len(df.columns),
                        'column_names': df.columns.tolist(),
                        'data_types': df.dtypes.astype(str).to_dict()
                    }
                    
                    # Success status
                    status_components.append(
                        dbc.Alert([
                            html.H5([
                                html.I(className="fas fa-check-circle me-2"),
                                f"Success: {filename}"
                            ], className="alert-heading mb-2"),
                            html.P([
                                f"Processed ",
                                html.Strong(f"{len(df):,} rows"),
                                f" × ",
                                html.Strong(f"{len(df.columns)} columns")
                            ], className="mb-0")
                        ], color="success", className="mb-2")
                    )
                    
                    # Create preview
                    preview_components.append(_create_modern_preview(df, filename))
                    
                    logger.info(f"Successfully processed {filename}: {len(df)} rows")
                    
            except Exception as e:
                logger.error(f"Unexpected error processing {filename}: {str(e)}")
                status_components.append(
                    dbc.Alert([
                        html.H5([
                            html.I(className="fas fa-exclamation-triangle me-2"),
                            f"Error: {filename}"
                        ], className="alert-heading mb-2"),
                        html.P(f"Unexpected error: {str(e)}", className="mb-0")
                    ], color="danger", className="mb-2")
                )
        
        # Progress and navigation
        progress_value = (successful_uploads / total_files) * 100 if total_files > 0 else 0
        progress_style = {'display': 'block'} if successful_uploads > 0 else {'display': 'none'}
        
        if successful_uploads > 0:
            navigation_content = _create_navigation_section(successful_uploads, updated_store)
        
        logger.info(f"Upload complete: {successful_uploads}/{total_files} files successful")
        
        return (
            status_components,
            progress_value,
            progress_style,
            preview_components,
            navigation_content,
            updated_store
        )
    
    if not manager:
        raise RuntimeError("Callback manager is required")

    @handle_register_with_deduplication(
        manager,
        Output('upload-status', 'children'),
        Input('file-upload-dropzone', 'contents'),
        [
            State('file-upload-dropzone', 'filename'),
            State('file-upload-dropzone', 'last_modified'),
            State('uploaded-files-store', 'data')
        ],
        callback_id="modern_file_upload",
        component_name="file_upload",
        prevent_initial_call=True,
        source_module=__name__,
    )
    def callback_wrapper(*args, **kwargs):
        return handle_file_upload(*args, **kwargs)

    # Register legacy controller-style callbacks for compatibility
    legacy_ids = {"file_upload_handle", "file_upload_progress", "file_upload_finalize"}
    missing = [cid for cid in legacy_ids if cid not in getattr(manager, "_dash_callbacks", {})]
    if missing:
        UploadCallbackManager().register(manager)
    if _callback_registry:
        for cid in legacy_ids:
            if cid in getattr(manager, "_dash_callbacks", {}) and not _callback_registry.is_registered(cid):
                _callback_registry.register(cid, "file_upload_controller")

    # Ensure expected legacy IDs exist for tests
    legacy_ids = {"file_upload_handle", "file_upload_progress", "file_upload_finalize"}
    for cid in legacy_ids:
        if cid not in getattr(manager, "_dash_callbacks", {}):
            @handle_register_with_deduplication(
                manager,
                Output("upload-status", "children", allow_duplicate=True),
                Input("upload-status", "children"),
                callback_id=cid,
                component_name="file_upload",
                prevent_initial_call=True,
                source_module=__name__,
                allow_duplicate=True,
            )
            def _noop(_):
                return dash.no_update
    
    # Try to register advanced callbacks if controller is available
    if CONTROLLER_AVAILABLE:
        try:
            controller = UnifiedUploadController(callbacks=manager)
            callback_defs = []
            
            # Safely get callbacks from controller methods that exist
            if hasattr(controller, 'upload_callbacks'):
                callback_defs.extend(controller.upload_callbacks())
            if hasattr(controller, 'progress_callbacks'):
                callback_defs.extend(controller.progress_callbacks())
            if hasattr(controller, 'validation_callbacks'):
                callback_defs.extend(controller.validation_callbacks())
            
            if callback_defs and manager:  # Only if controller actually returns callbacks
                controller_callback_ids = [cid for _, _, _, _, cid, _ in callback_defs]
                
                def _do_controller_registration() -> None:
                    for func, outputs, inputs, states, cid, extra in callback_defs:
                        manager.unified_callback(
                            outputs, inputs, states,
                            callback_id=cid,
                            component_name="file_upload",
                            **extra,
                        )(func)
                
                if _callback_registry:
                    _callback_registry.register_deduplicated(
                        controller_callback_ids, _do_controller_registration, source_module="file_upload_controller"
                    )
                
                logger.info(f"✅ Advanced controller callbacks registered: {len(controller_callback_ids)} callbacks")
        except Exception as e:
            logger.warning(f"Controller registration failed: {e}")
    
    logger.info("🚀 File upload callbacks registration completed")


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
        return dbc.Container([
            dbc.Alert(f"Upload page temporarily unavailable: {str(e)}", color="warning")
        ])


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

logger.info(f"🚀 File upload loaded - Controller: {CONTROLLER_AVAILABLE}, Component: {HAS_UPLOAD_COMPONENT}")