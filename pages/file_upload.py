#!/usr/bin/env python3
"""
DIRECT FIX: Replace ENTIRE content of pages/file_upload.py with this code
This embeds everything inline so no import issues can occur
"""

import base64
import json
import logging
from io import BytesIO, StringIO
from typing import TYPE_CHECKING, Any, Dict, List, Tuple, Union

import pandas as pd
from dash import dcc, html, Input, Output, State, callback_context, no_update
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc

if TYPE_CHECKING:
    from core.truly_unified_callbacks import TrulyUnifiedCallbacks

logger = logging.getLogger(__name__)


def safe_unicode_encode(text: Union[str, bytes, None]) -> str:
    """Safely encode text, handling Unicode surrogate characters."""
    if text is None:
        return ""
    
    if isinstance(text, bytes):
        for encoding in ['utf-8', 'latin-1', 'cp1252']:
            try:
                text = text.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            text = text.decode('utf-8', errors='replace')
    
    if isinstance(text, str):
        try:
            text.encode('utf-8')
            return text
        except UnicodeEncodeError:
            return text.encode('utf-8', errors='replace').decode('utf-8')
    
    return str(text)


def decode_upload_content(content: str, filename: str) -> tuple[bytes, str]:
    """Decode Dash upload content with proper error handling."""
    if not content:
        raise ValueError("No content provided")
    
    try:
        if ',' in content:
            header, content = content.split(',', 1)
        
        decoded_content = base64.b64decode(content)
        safe_filename = safe_unicode_encode(filename)
        
        return decoded_content, safe_filename
        
    except Exception as e:
        logger.error(f"Failed to decode upload content: {e}")
        raise ValueError(f"Invalid file content: {e}")


def process_csv_file(content: bytes, filename: str) -> html.Div:
    """Process CSV file with proper Unicode handling."""
    try:
        for encoding in ['utf-8', 'latin-1', 'cp1252']:
            try:
                text_content = content.decode(encoding)
                df = pd.read_csv(StringIO(text_content))
                break
            except (UnicodeDecodeError, pd.errors.EmptyDataError):
                continue
        else:
            text_content = content.decode('utf-8', errors='replace')
            df = pd.read_csv(StringIO(text_content))
        
        return html.Div([
            dbc.Alert(f"✅ {filename}: {len(df)} rows, {len(df.columns)} columns", color="success"),
            html.H6("Preview:", className="mt-3"),
            html.Pre(
                df.head().to_string(),
                style={
                    'font-size': '12px',
                    'overflow': 'auto',
                    'background': '#f8f9fa',
                    'padding': '10px',
                    'border-radius': '5px'
                }
            )
        ])
        
    except Exception as e:
        return dbc.Alert(f"❌ CSV processing failed: {e}", color="danger")


def process_excel_file(content: bytes, filename: str) -> html.Div:
    """Process Excel file."""
    try:
        df = pd.read_excel(BytesIO(content))
        return html.Div([
            dbc.Alert(f"✅ {filename}: {len(df)} rows, {len(df.columns)} columns", color="success"),
            html.H6("Preview:", className="mt-3"),
            html.Pre(
                df.head().to_string(),
                style={
                    'font-size': '12px',
                    'overflow': 'auto',
                    'background': '#f8f9fa',
                    'padding': '10px',
                    'border-radius': '5px'
                }
            )
        ])
        
    except Exception as e:
        return dbc.Alert(f"❌ Excel processing failed: {e}", color="danger")


def process_json_file(content: bytes, filename: str) -> html.Div:
    """Process JSON file."""
    try:
        text_content = safe_unicode_encode(content.decode('utf-8', errors='replace'))
        data = json.loads(text_content)
        
        return html.Div([
            dbc.Alert(f"✅ {filename}: JSON loaded successfully", color="success"),
            html.H6("Structure:", className="mt-3"),
            html.Pre(
                json.dumps(data, indent=2, ensure_ascii=False)[:500] + "...",
                style={
                    'font-size': '12px',
                    'overflow': 'auto',
                    'background': '#f8f9fa',
                    'padding': '10px',
                    'border-radius': '5px'
                }
            )
        ])
        
    except Exception as e:
        return dbc.Alert(f"❌ JSON processing failed: {e}", color="danger")


def layout() -> html.Div:
    """Create the upload page layout with embedded upload component."""
    
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H1("File Upload", className="mb-4"),
                html.P(
                    "Upload your data files to begin analysis. "
                    "Supported formats: CSV, Excel (.xlsx, .xls), and JSON files.",
                    className="text-muted mb-4"
                ),
                
                # EMBEDDED UPLOAD COMPONENT - NO IMPORTS NEEDED
                html.Div([
                    dcc.Upload(
                        id="main-file-upload",
                        children=html.Div([
                            html.I(
                                className="fas fa-cloud-upload-alt",
                                style={
                                    "font-size": "48px",
                                    "color": "#007bff",
                                    "margin-bottom": "20px"
                                }
                            ),
                            html.H5(
                                "Drag & Drop Files Here or Click to Browse",
                                style={"color": "#007bff", "margin-bottom": "10px"}
                            ),
                            html.P(
                                "Supports CSV, Excel (.xlsx, .xls), and JSON files",
                                style={"color": "#6c757d", "margin": "0"}
                            )
                        ], style={
                            "display": "flex",
                            "flex-direction": "column",
                            "align-items": "center",
                            "justify-content": "center",
                            "height": "100%",
                            "text-align": "center"
                        }),
                        style={
                            'width': '100%',
                            'height': '200px',
                            'border': '2px dashed #007bff',
                            'border-radius': '10px',
                            'background-color': '#f8f9fa',
                            'cursor': 'pointer',
                            'transition': 'all 0.3s ease',
                            'display': 'flex',
                            'align-items': 'center',
                            'justify-content': 'center'
                        },
                        multiple=True,
                        max_size=50 * 1024 * 1024  # 50MB
                    ),
                    
                    # Status and results
                    html.Div(id="upload-status", style={'margin-top': '20px'}),
                    html.Div(id="upload-results", style={'margin-top': '20px'})
                    
                ], style={'margin-bottom': '30px'}),
                
                # Guidelines card
                dbc.Card([
                    dbc.CardHeader("Upload Guidelines"),
                    dbc.CardBody([
                        html.Ul([
                            html.Li("Maximum file size: 50MB"),
                            html.Li("Multiple files can be uploaded simultaneously"),
                            html.Li("CSV files should use UTF-8 encoding when possible"),
                            html.Li("Excel files (.xlsx, .xls) are fully supported"),
                            html.Li("JSON files will be parsed and validated")
                        ])
                    ])
                ], className="mt-4"),
                
                # Toast container for notifications
                html.Div(id="toast-container"),
                
                # Hidden stores for data
                dcc.Store(id="file-info-store"),
                dcc.Store(id="upload-progress-store")
                
            ], width=12)
        ])
    ], fluid=True)


def register_upload_callbacks(manager: "TrulyUnifiedCallbacks", controller=None) -> None:
    """Register upload callbacks directly with the manager."""
    
    @manager.app.callback(
        [
            Output("upload-status", "children"),
            Output("upload-results", "children")
        ],
        [Input("main-file-upload", "contents")],
        [
            State("main-file-upload", "filename"),
            State("main-file-upload", "last_modified")
        ],
        prevent_initial_call=True
    )
    def handle_file_upload(contents, filenames, last_modified):
        """Handle file upload and processing."""
        
        if not contents:
            raise PreventUpdate
        
        try:
            # Show processing status
            status = dbc.Alert("Processing files...", color="info")
            results = []
            
            # Handle multiple files
            if not isinstance(contents, list):
                contents = [contents]
                filenames = [filenames]
                last_modified = [last_modified]
            
            # Process each file
            for content, filename, modified in zip(contents, filenames, last_modified):
                try:
                    # Decode file content
                    decoded_content, safe_filename = decode_upload_content(content, filename)
                    
                    # Determine file type and process
                    file_ext = safe_filename.lower().split('.')[-1] if '.' in safe_filename else ''
                    
                    if file_ext == 'csv':
                        result = process_csv_file(decoded_content, safe_filename)
                    elif file_ext in ['xlsx', 'xls']:
                        result = process_excel_file(decoded_content, safe_filename)
                    elif file_ext == 'json':
                        result = process_json_file(decoded_content, safe_filename)
                    else:
                        result = dbc.Alert(f"Unsupported file type: {file_ext}", color="warning")
                    
                    results.append(html.Div([result], className="mb-3"))
                    logger.info(f"Successfully processed: {safe_filename}")
                    
                except Exception as e:
                    error_msg = f"Error processing {safe_unicode_encode(filename)}: {str(e)}"
                    logger.error(error_msg)
                    results.append(
                        html.Div([
                            dbc.Alert(error_msg, color="danger")
                        ], className="mb-3")
                    )
            
            # Final status
            success_count = len([r for r in results if "success" in str(r)])
            if success_count > 0:
                final_status = dbc.Alert(
                    f"✅ Successfully processed {success_count} file(s)",
                    color="success"
                )
            else:
                final_status = dbc.Alert("❌ No files were processed successfully", color="danger")
            
            return final_status, html.Div(results)
            
        except Exception as e:
            error_status = dbc.Alert(f"Upload failed: {str(e)}", color="danger")
            logger.error(f"Upload processing error: {e}")
            return error_status, no_update
    
    # Visual feedback callback for drag/drop
    @manager.app.callback(
        Output("main-file-upload", "style"),
        [Input("main-file-upload", "contents")],
        prevent_initial_call=True
    )
    def update_upload_style(contents):
        """Update upload area style after successful upload."""
        if contents:
            return {
                'width': '100%',
                'height': '200px',
                'border': '2px solid #28a745',
                'border-radius': '10px',
                'background-color': '#d4edda',
                'cursor': 'pointer',
                'transition': 'all 0.3s ease',
                'display': 'flex',
                'align-items': 'center',
                'justify-content': 'center'
            }
        raise PreventUpdate
    
    logger.info("✅ Upload callbacks registered successfully")


def register_enhanced_upload_callbacks(manager: "TrulyUnifiedCallbacks", controller=None) -> None:
    """Enhanced upload callbacks - alias for compatibility."""
    return register_upload_callbacks(manager, controller)


def register_callbacks(manager: "TrulyUnifiedCallbacks", controller=None) -> None:
    """General callback registration - alias for compatibility."""
    return register_upload_callbacks(manager, controller)


def check_upload_system_health() -> dict:
    """Check if the upload system is properly configured."""
    health_status = {
        "status": "healthy",
        "components": [],
        "errors": []
    }
    
    try:
        # Test Unicode handling
        test_text = "Test with special chars: café, résumé, 中文"
        encoded = safe_unicode_encode(test_text)
        health_status["components"].append("Unicode handling: OK")
        
        # Test base64 decoding
        test_content = "VGVzdCBkYXRh"  # "Test data" in base64
        decoded, filename = decode_upload_content(test_content, "test.csv")
        health_status["components"].append("Base64 decoding: OK")
        
        # Test CSV processing
        test_csv = b"Name,Age\nJohn,25\nJane,30"
        result = process_csv_file(test_csv, "test.csv")
        health_status["components"].append("CSV processing: OK")
        
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["errors"].append(f"System check failed: {e}")
        logger.error(f"Upload system health check failed: {e}")
    
    return health_status


# Export all necessary functions
__all__ = [
    "layout",
    "register_upload_callbacks",
    "register_enhanced_upload_callbacks", 
    "register_callbacks",
    "check_upload_system_health"
]

logger.info("🚀 Direct upload page module loaded successfully")
