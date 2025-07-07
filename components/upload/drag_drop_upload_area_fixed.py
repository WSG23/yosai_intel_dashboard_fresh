#!/usr/bin/env python3
"""
Fixed file upload component with proper Unicode handling and working callbacks.
Replaces components/upload/drag_drop_upload_area.py
"""
import base64
import logging
from typing import Any, Dict, List, Optional, Union

from dash import dcc, html, Input, Output, State, callback, no_update, ctx
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc

logger = logging.getLogger(__name__)


def safe_unicode_encode(text: Union[str, bytes, None]) -> str:
    """
    Safely encode text, handling Unicode surrogate characters.
    
    Args:
        text: Input text that may contain problematic Unicode
        
    Returns:
        Safe UTF-8 encoded string
    """
    if text is None:
        return ""
    
    if isinstance(text, bytes):
        # Try different encodings for bytes
        for encoding in ['utf-8', 'latin-1', 'cp1252']:
            try:
                text = text.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            # Fallback: decode with errors='replace'
            text = text.decode('utf-8', errors='replace')
    
    if isinstance(text, str):
        # Handle surrogate characters that can't be encoded in UTF-8
        try:
            # Test if string can be encoded to UTF-8
            text.encode('utf-8')
            return text
        except UnicodeEncodeError:
            # Replace problematic characters
            return text.encode('utf-8', errors='replace').decode('utf-8')
    
    return str(text)


def decode_upload_content(content: str, filename: str) -> tuple[bytes, str]:
    """
    Decode Dash upload content with proper error handling.
    
    Args:
        content: Base64 encoded content from Dash upload
        filename: Original filename
        
    Returns:
        Tuple of (decoded_content, safe_filename)
        
    Raises:
        ValueError: If content cannot be decoded
    """
    if not content:
        raise ValueError("No content provided")
    
    try:
        # Remove data URL prefix if present
        if ',' in content:
            header, content = content.split(',', 1)
        
        # Decode base64 content
        decoded_content = base64.b64decode(content)
        safe_filename = safe_unicode_encode(filename)
        
        return decoded_content, safe_filename
        
    except Exception as e:
        logger.error(f"Failed to decode upload content: {e}")
        raise ValueError(f"Invalid file content: {e}")


class FileUploadComponent:
    """
    Modular file upload component with consolidated callbacks.
    """
    
    def __init__(self, upload_id: str = "file-upload"):
        self.upload_id = upload_id
        self.status_id = f"{upload_id}-status"
        self.progress_id = f"{upload_id}-progress"
        self.results_id = f"{upload_id}-results"
        
    def render(self) -> html.Div:
        """Render the complete upload interface."""
        return html.Div([
            # Upload component
            dcc.Upload(
                id=self.upload_id,
                children=html.Div([
                    html.I(
                        className="fas fa-cloud-upload-alt fa-3x mb-3",
                        style={"color": "#007bff"}
                    ),
                    html.H5("Drag & Drop or Click to Upload", className="mb-2"),
                    html.P(
                        "Supports CSV, Excel (.xlsx, .xls), JSON files",
                        className="text-muted mb-0"
                    )
                ]),
                style={
                    'width': '100%',
                    'height': '200px',
                    'lineHeight': '200px',
                    'borderWidth': '2px',
                    'borderStyle': 'dashed',
                    'borderRadius': '10px',
                    'borderColor': '#007bff',
                    'textAlign': 'center',
                    'backgroundColor': '#f8f9fa',
                    'cursor': 'pointer',
                    'transition': 'all 0.3s ease'
                },
                multiple=True,
                max_size=50 * 1024 * 1024  # 50MB limit
            ),
            
            # Status display
            html.Div(id=self.status_id, style={'margin-top': '10px'}),
            
            # Progress bar
            dbc.Progress(
                id=self.progress_id,
                value=0,
                style={'margin-top': '10px', 'display': 'none'}
            ),
            
            # Results display
            html.Div(id=self.results_id, style={'margin-top': '20px'})
        ])
    
    def register_callbacks(self, app):
        """Register all upload-related callbacks."""
        
        @app.callback(
            [
                Output(self.status_id, 'children'),
                Output(self.progress_id, 'style'),
                Output(self.progress_id, 'value'),
                Output(self.results_id, 'children')
            ],
            [Input(self.upload_id, 'contents')],
            [
                State(self.upload_id, 'filename'),
                State(self.upload_id, 'last_modified')
            ],
            prevent_initial_call=True
        )
        def handle_upload(contents, filenames, last_modified):
            """Consolidated callback for handling file uploads."""
            
            if not contents:
                raise PreventUpdate
            
            # Show progress
            progress_style = {'margin-top': '10px', 'display': 'block'}
            status = dbc.Alert("Processing files...", color="info")
            
            try:
                results = []
                
                # Handle multiple files
                if not isinstance(contents, list):
                    contents = [contents]
                    filenames = [filenames]
                    last_modified = [last_modified]
                
                for i, (content, filename, modified) in enumerate(zip(contents, filenames, last_modified)):
                    # Update progress
                    progress = int((i / len(contents)) * 100)
                    
                    try:
                        # Decode file content
                        decoded_content, safe_filename = decode_upload_content(content, filename)
                        
                        # Process file based on type
                        result = self._process_file(decoded_content, safe_filename)
                        results.append(result)
                        
                        logger.info(f"Successfully processed: {safe_filename}")
                        
                    except Exception as e:
                        error_msg = f"Error processing {safe_unicode_encode(filename)}: {str(e)}"
                        logger.error(error_msg)
                        results.append(
                            dbc.Alert(error_msg, color="danger", className="mb-2")
                        )
                
                # Final status
                success_status = dbc.Alert(
                    f"Successfully processed {len([r for r in results if not isinstance(r, dbc.Alert)])} files",
                    color="success"
                )
                
                progress_style['display'] = 'none'
                
                return success_status, progress_style, 100, html.Div(results)
                
            except Exception as e:
                error_status = dbc.Alert(f"Upload failed: {str(e)}", color="danger")
                progress_style['display'] = 'none'
                return error_status, progress_style, 0, no_update
        
        @app.callback(
            Output(self.upload_id, 'style'),
            [Input(self.upload_id, 'contents')],
            prevent_initial_call=True
        )
        def update_upload_style(contents):
            """Update upload area style on hover/drop."""
            if contents:
                return {
                    'width': '100%',
                    'height': '200px',
                    'lineHeight': '200px',
                    'borderWidth': '2px',
                    'borderStyle': 'dashed',
                    'borderRadius': '10px',
                    'borderColor': '#28a745',
                    'textAlign': 'center',
                    'backgroundColor': '#d4edda',
                    'cursor': 'pointer',
                    'transition': 'all 0.3s ease'
                }
            raise PreventUpdate
    
    def _process_file(self, content: bytes, filename: str) -> html.Div:
        """
        Process individual file content.
        
        Args:
            content: Raw file content
            filename: Safe filename
            
        Returns:
            Processed file display component
        """
        try:
            file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
            
            if file_ext == 'csv':
                return self._process_csv(content, filename)
            elif file_ext in ['xlsx', 'xls']:
                return self._process_excel(content, filename)
            elif file_ext == 'json':
                return self._process_json(content, filename)
            else:
                return dbc.Alert(
                    f"Unsupported file type: {file_ext}",
                    color="warning",
                    className="mb-2"
                )
                
        except Exception as e:
            return dbc.Alert(
                f"Error processing {filename}: {str(e)}",
                color="danger",
                className="mb-2"
            )
    
    def _process_csv(self, content: bytes, filename: str) -> html.Div:
        """Process CSV file with proper Unicode handling."""
        import pandas as pd
        from io import StringIO
        
        try:
            # Try different encodings
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    text_content = content.decode(encoding)
                    df = pd.read_csv(StringIO(text_content))
                    break
                except (UnicodeDecodeError, pd.errors.EmptyDataError):
                    continue
            else:
                # Fallback with error replacement
                text_content = content.decode('utf-8', errors='replace')
                df = pd.read_csv(StringIO(text_content))
            
            return html.Div([
                dbc.Alert(f"✅ {filename}: {len(df)} rows, {len(df.columns)} columns", color="success"),
                html.Div([
                    html.H6("Preview:"),
                    html.Pre(df.head().to_string(), style={'font-size': '12px', 'overflow': 'auto'})
                ])
            ])
            
        except Exception as e:
            raise ValueError(f"CSV processing failed: {e}")
    
    def _process_excel(self, content: bytes, filename: str) -> html.Div:
        """Process Excel file."""
        import pandas as pd
        from io import BytesIO
        
        try:
            df = pd.read_excel(BytesIO(content))
            return html.Div([
                dbc.Alert(f"✅ {filename}: {len(df)} rows, {len(df.columns)} columns", color="success"),
                html.Div([
                    html.H6("Preview:"),
                    html.Pre(df.head().to_string(), style={'font-size': '12px', 'overflow': 'auto'})
                ])
            ])
            
        except Exception as e:
            raise ValueError(f"Excel processing failed: {e}")
    
    def _process_json(self, content: bytes, filename: str) -> html.Div:
        """Process JSON file."""
        import json
        
        try:
            text_content = safe_unicode_encode(content.decode('utf-8', errors='replace'))
            data = json.loads(text_content)
            
            return html.Div([
                dbc.Alert(f"✅ {filename}: JSON loaded successfully", color="success"),
                html.Div([
                    html.H6("Structure:"),
                    html.Pre(
                        json.dumps(data, indent=2, ensure_ascii=False)[:500] + "...",
                        style={'font-size': '12px', 'overflow': 'auto'}
                    )
                ])
            ])
            
        except Exception as e:
            raise ValueError(f"JSON processing failed: {e}")


# Standalone function for easy integration
def create_upload_component(upload_id: str = "file-upload") -> FileUploadComponent:
    """Create a new upload component instance."""
    return FileUploadComponent(upload_id)


# Export for module-level usage
__all__ = ['FileUploadComponent', 'create_upload_component', 'safe_unicode_encode', 'decode_upload_content']
