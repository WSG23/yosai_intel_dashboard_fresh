#!/usr/bin/env python3
"""
Simple file upload page - Basic version that just shows the upload area
"""
import base64
import json
import logging
from io import BytesIO, StringIO
from typing import TYPE_CHECKING, Any, Dict, List, Tuple, Union

import pandas as pd
from dash import dcc, html, Input, Output, State, no_update
from dash.exceptions import PreventUpdate

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


def layout() -> html.Div:
    """Create a simple upload page layout."""
    return html.Div([
        # Container with max width
        html.Div([
            # Header
            html.H1("File Upload", style={
                'margin-bottom': '20px',
                'color': '#333',
                'text-align': 'center'
            }),
            
            html.P([
                "Upload your data files to begin analysis. ",
                html.Br(),
                "Supported formats: CSV, Excel (.xlsx, .xls), and JSON files."
            ], style={
                'color': '#6c757d',
                'margin-bottom': '30px',
                'text-align': 'center'
            }),
            
            # SIMPLE UPLOAD COMPONENT - Using dcc.Upload directly
            dcc.Upload(
                id="file-upload-main",
                children=html.Div([
                    html.I(
                        className="fas fa-cloud-upload-alt",
                        style={
                            'font-size': '48px',
                            'color': '#007bff',
                            'display': 'block',
                            'margin-bottom': '15px'
                        }
                    ),
                    html.H4(
                        "Drag & Drop Files Here",
                        style={
                            'margin-bottom': '10px',
                            'color': '#007bff'
                        }
                    ),
                    html.P(
                        "or click to select files",
                        style={
                            'color': '#6c757d',
                            'margin': '0'
                        }
                    ),
                    html.P([
                        html.Small("Supports: CSV, Excel (.xlsx, .xls), JSON files")
                    ], style={
                        'color': '#999',
                        'margin-top': '10px'
                    })
                ], style={
                    'text-align': 'center',
                    'padding': '40px 20px'
                }),
                style={
                    'width': '100%',
                    'height': '250px',
                    'border': '3px dashed #007bff',
                    'border-radius': '15px',
                    'background-color': '#f8f9fa',
                    'cursor': 'pointer',
                    'transition': 'all 0.3s ease',
                    'margin-bottom': '30px',
                    'display': 'flex',
                    'align-items': 'center',
                    'justify-content': 'center'
                },
                multiple=True,
                max_size=50 * 1024 * 1024  # 50MB
            ),
            
            # Results area
            html.Div(id="upload-output", style={
                'margin-top': '20px',
                'min-height': '50px'
            }),
            
            # Guidelines card
            html.Div([
                html.H5("\ud83d\udccb Upload Guidelines", style={
                    'margin-bottom': '15px',
                    'color': '#495057'
                }),
                html.Ul([
                    html.Li("Maximum file size: 50MB per file"),
                    html.Li("Multiple files can be uploaded at once"),
                    html.Li("CSV files work best with UTF-8 encoding"),
                    html.Li("Excel files (.xlsx, .xls) are fully supported"),
                    html.Li("JSON files will be validated and parsed")
                ], style={'color': '#6c757d'})
            ], style={
                'background': '#ffffff',
                'padding': '25px',
                'border-radius': '10px',
                'border': '1px solid #dee2e6',
                'box-shadow': '0 2px 4px rgba(0,0,0,0.1)',
                'margin-top': '40px'
            })
            
        ], style={
            'max-width': '800px',
            'margin': '0 auto',
            'padding': '40px 20px',
            'min-height': '100vh'
        })
    ], style={
        'background': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        'min-height': '100vh'
    })


def register_upload_callbacks(manager: "TrulyUnifiedCallbacks", controller=None) -> None:
    """Register simple upload callback."""
    
    @manager.unified_callback(
        Output("upload-output", "children"),
        Input("file-upload-main", "contents"),
        State("file-upload-main", "filename"),
        callback_id="simple_upload",
        component_name="file_upload",
        prevent_initial_call=True
    )
    def handle_upload(contents, filenames):
        """Simple upload handler."""
        if not contents:
            raise PreventUpdate
        
        # Convert to lists if single file
        if not isinstance(contents, list):
            contents = [contents]
            filenames = [filenames]
        
        results = []
        
        for content, filename in zip(contents, filenames):
            try:
                # Decode content
                if ',' in content:
                    header, content = content.split(',', 1)
                
                decoded = base64.b64decode(content)
                safe_filename = safe_unicode_encode(filename)
                
                # Simple processing based on file type
                file_ext = safe_filename.lower().split('.')[-1] if '.' in safe_filename else ''
                
                if file_ext == 'csv':
                    # Try to read CSV
                    try:
                        text_content = decoded.decode('utf-8', errors='replace')
                        df = pd.read_csv(StringIO(text_content))
                        
                        results.append(html.Div([
                            html.H6(f"\u2705 {safe_filename}", style={'color': 'green', 'margin-bottom': '10px'}),
                            html.P(f"\ud83d\udcca {len(df)} rows, {len(df.columns)} columns"),
                            html.Details([
                                html.Summary("\ud83d\udccb Preview (click to expand)"),
                                html.Pre(
                                    df.head().to_string(),
                                    style={
                                        'background': '#f8f9fa',
                                        'padding': '10px',
                                        'border-radius': '5px',
                                        'font-size': '12px',
                                        'overflow': 'auto',
                                        'max-height': '300px'
                                    }
                                )
                            ])
                        ], style={
                            'background': '#d4edda',
                            'border': '1px solid #c3e6cb',
                            'border-radius': '8px',
                            'padding': '15px',
                            'margin': '10px 0'
                        }))
                        
                    except Exception as e:
                        results.append(html.Div([
                            html.H6(f"\u274c {safe_filename}", style={'color': 'red'}),
                            html.P(f"CSV error: {str(e)}")
                        ], style={
                            'background': '#f8d7da',
                            'border': '1px solid #f5c6cb',
                            'border-radius': '8px',
                            'padding': '15px',
                            'margin': '10px 0'
                        }))
                
                elif file_ext in ['xlsx', 'xls']:
                    # Try to read Excel
                    try:
                        df = pd.read_excel(BytesIO(decoded))
                        
                        results.append(html.Div([
                            html.H6(f"\u2705 {safe_filename}", style={'color': 'green', 'margin-bottom': '10px'}),
                            html.P(f"\ud83d\udcca {len(df)} rows, {len(df.columns)} columns"),
                            html.Details([
                                html.Summary("\ud83d\udccb Preview (click to expand)"),
                                html.Pre(
                                    df.head().to_string(),
                                    style={
                                        'background': '#f8f9fa',
                                        'padding': '10px',
                                        'border-radius': '5px',
                                        'font-size': '12px',
                                        'overflow': 'auto',
                                        'max-height': '300px'
                                    }
                                )
                            ])
                        ], style={
                            'background': '#d4edda',
                            'border': '1px solid #c3e6cb',
                            'border-radius': '8px',
                            'padding': '15px',
                            'margin': '10px 0'
                        }))
                        
                    except Exception as e:
                        results.append(html.Div([
                            html.H6(f"\u274c {safe_filename}", style={'color': 'red'}),
                            html.P(f"Excel error: {str(e)}")
                        ], style={
                            'background': '#f8d7da',
                            'border': '1px solid #f5c6cb',
                            'border-radius': '8px',
                            'padding': '15px',
                            'margin': '10px 0'
                        }))
                
                elif file_ext == 'json':
                    # Try to read JSON
                    try:
                        text_content = decoded.decode('utf-8', errors='replace')
                        data = json.loads(text_content)
                        
                        results.append(html.Div([
                            html.H6(f"\u2705 {safe_filename}", style={'color': 'green', 'margin-bottom': '10px'}),
                            html.P(f"\ud83d\udcc4 JSON loaded successfully"),
                            html.Details([
                                html.Summary("\ud83d\udccb Structure (click to expand)"),
                                html.Pre(
                                    json.dumps(data, indent=2, ensure_ascii=False)[:1000] + "..." if len(str(data)) > 1000 else json.dumps(data, indent=2, ensure_ascii=False),
                                    style={
                                        'background': '#f8f9fa',
                                        'padding': '10px',
                                        'border-radius': '5px',
                                        'font-size': '12px',
                                        'overflow': 'auto',
                                        'max-height': '300px'
                                    }
                                )
                            ])
                        ], style={
                            'background': '#d4edda',
                            'border': '1px solid #c3e6cb',
                            'border-radius': '8px',
                            'padding': '15px',
                            'margin': '10px 0'
                        }))
                        
                    except Exception as e:
                        results.append(html.Div([
                            html.H6(f"\u274c {safe_filename}", style={'color': 'red'}),
                            html.P(f"JSON error: {str(e)}")
                        ], style={
                            'background': '#f8d7da',
                            'border': '1px solid #f5c6cb',
                            'border-radius': '8px',
                            'padding': '15px',
                            'margin': '10px 0'
                        }))
                
                else:
                    results.append(html.Div([
                        html.H6(f"\u26a0\ufe0f {safe_filename}", style={'color': 'orange'}),
                        html.P(f"Unsupported file type: .{file_ext}")
                    ], style={
                        'background': '#fff3cd',
                        'border': '1px solid #ffeaa7',
                        'border-radius': '8px',
                        'padding': '15px',
                        'margin': '10px 0'
                    }))
                
            except Exception as e:
                results.append(html.Div([
                    html.H6(f"\u274c {safe_unicode_encode(filename)}", style={'color': 'red'}),
                    html.P(f"Processing error: {str(e)}")
                ], style={
                    'background': '#f8d7da',
                    'border': '1px solid #f5c6cb',
                    'border-radius': '8px',
                    'padding': '15px',
                    'margin': '10px 0'
                }))
        
        if results:
            return html.Div([
                html.H5(f"\ud83d\udcc1 Upload Results ({len(results)} files)", style={
                    'margin-bottom': '20px',
                    'color': '#495057'
                }),
                *results
            ])
        else:
            return html.Div("No files processed.", style={'color': '#6c757d'})
    
    logger.info("\u2705 Simple upload callback registered")


def register_enhanced_upload_callbacks(manager: "TrulyUnifiedCallbacks", controller=None) -> None:
    """Alias for compatibility."""
    return register_upload_callbacks(manager, controller)


def register_callbacks(manager: "TrulyUnifiedCallbacks", controller=None) -> None:
    """Alias for compatibility."""
    return register_upload_callbacks(manager, controller)


def check_upload_system_health() -> dict:
    """Check system health."""
    return {
        "status": "healthy",
        "components": ["Simple upload layout: OK"],
        "errors": []
    }


# Export functions
__all__ = [
    "layout",
    "register_upload_callbacks",
    "register_enhanced_upload_callbacks", 
    "register_callbacks",
    "check_upload_system_health"
]

logger.info("\ud83d\ude80 Simple upload page loaded successfully")
