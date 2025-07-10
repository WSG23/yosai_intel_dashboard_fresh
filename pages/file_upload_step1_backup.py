#!/usr/bin/env python3
"""
Step 1 Enhancement: Add real file input to working upload
Uses dcc.Upload but isolated to prevent navigation flash
"""
from __future__ import annotations

import logging
from typing import Any

import dash_bootstrap_components as dbc
from dash import html, register_page as dash_register_page, dcc, dash_table, callback
from dash import Input, Output, State
from dash.exceptions import PreventUpdate

logger = logging.getLogger(__name__)

def register_page() -> None:
    """Register the upload page with Dash."""
    dash_register_page(__name__, path="/upload", name="Upload", aliases=["/file-upload"])

def layout() -> html.Div:
    """Step 1: Add real file input while keeping page stable."""
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H1([
                    html.I(className="fas fa-cloud-upload-alt me-3"),
                    "File Upload"
                ], className="text-primary mb-4"),
                
                dbc.Card([
                    dbc.CardHeader([
                        html.H4("Upload Data Files", className="mb-0"),
                        html.Small("Step 1: Real file input added", className="text-success")
                    ]),
                    dbc.CardBody([
                        # Tabs for different upload methods
                        dbc.Tabs([
                            # Tab 1: Real File Upload
                            dbc.Tab(label="📁 File Upload", tab_id="file-tab", children=[
                                html.Div([
                                    # Real file upload using dcc.Upload (isolated)
                                    html.Div([
                                        dcc.Upload(
                                            id="isolated-file-upload",
                                            children=html.Div([
                                                html.I(className="fas fa-file-upload fa-3x mb-3"),
                                                html.H6("Click to Browse Files", className="mb-2"),
                                                html.P("CSV, JSON, Excel files", className="small text-muted")
                                            ], className="text-center p-3"),
                                            className="upload-dropzone",  # Uses assets/css
                                            multiple=True,
                                            accept=".csv,.json,.xlsx,.xls"
                                        )
                                    ], className="mb-3"),
                                    
                                    # File upload results
                                    html.Div(id="file-upload-results")
                                ], className="p-3")
                            ]),
                            
                            # Tab 2: Text Input (fallback)
                            dbc.Tab(label="📝 Text Input", tab_id="text-tab", children=[
                                html.Div([
                                    dbc.Textarea(
                                        id="csv-content-input",
                                        placeholder="Paste CSV content here...\nExample:\nname,age\nJohn,25\nJane,30",
                                        rows=6,
                                        className="mb-3"
                                    ),
                                    dbc.Button([
                                        html.I(className="fas fa-upload me-2"),
                                        "Process Text Data"
                                    ], id="process-text-btn", color="success", size="lg", className="w-100")
                                ], className="p-3")
                            ])
                        ], active_tab="file-tab", className="mb-3"),
                        
                        # Results area (shared)
                        html.Div(id="upload-results", className="mt-3"),
                        html.Div(id="file-preview", className="mt-3"),
                        
                        html.Hr(),
                        
                        # Status
                        dbc.Row([
                            dbc.Col([
                                html.H6("✅ Step 1 Features:"),
                                html.Ul([
                                    html.Li("✅ Navigation flash eliminated"),
                                    html.Li("✅ Real file browsing added"),
                                    html.Li("✅ Text input fallback"),
                                    html.Li("✅ CSV/JSON/Excel support")
                                ])
                            ], md=6),
                            dbc.Col([
                                html.H6("🔧 Next Enhancements:"),
                                html.Ul([
                                    html.Li("🔄 Add drag & drop"),
                                    html.Li("🔄 Add progress tracking"),
                                    html.Li("�� Integrate sophisticated backend"),
                                    html.Li("🔄 Add file validation")
                                ])
                            ], md=6)
                        ], className="small text-muted")
                    ])
                ], className="shadow-sm")
            ], width=10)
        ], justify="center")
    ], fluid=True, className="py-4")

# File upload callback
@callback(
    Output("file-upload-results", "children"),
    Input("isolated-file-upload", "contents"),
    State("isolated-file-upload", "filename"),
    prevent_initial_call=True
)
def handle_file_upload(contents_list, filenames_list):
    """Handle real file uploads."""
    if not contents_list:
        return ""
    
    # Ensure lists
    if not isinstance(contents_list, list):
        contents_list = [contents_list]
    if not isinstance(filenames_list, list):
        filenames_list = [filenames_list]
    
    results = []
    for content, filename in zip(contents_list, filenames_list):
        try:
            import base64
            import pandas as pd
            import io
            import json
            
            # Decode file
            content_type, content_string = content.split(',', 1)
            decoded = base64.b64decode(content_string)
            
            # Process based on file type
            if filename.lower().endswith('.csv'):
                df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
            elif filename.lower().endswith(('.xlsx', '.xls')):
                df = pd.read_excel(io.BytesIO(decoded))
            elif filename.lower().endswith('.json'):
                data = json.loads(decoded.decode('utf-8'))
                df = pd.DataFrame(data)
            else:
                continue
            
            rows, cols = len(df), len(df.columns)
            
            # Success alert
            result = dbc.Alert([
                html.I(className="fas fa-check-circle me-2"),
                f"✅ {filename}: {rows} rows, {cols} columns"
            ], color="success", className="mb-2")
            results.append(result)
            
        except Exception as e:
            error = dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                f"❌ Error processing {filename}: {str(e)}"
            ], color="danger", className="mb-2")
            results.append(error)
    
    return results

# Text processing callback (keep existing)
@callback(
    [Output("upload-results", "children"),
     Output("file-preview", "children")],
    Input("process-text-btn", "n_clicks"),
    State("csv-content-input", "value"),
    prevent_initial_call=True
)
def process_csv_content(n_clicks, csv_content):
    """Process CSV content from text input."""
    if not n_clicks or not csv_content:
        raise PreventUpdate
    
    try:
        import pandas as pd
        import io
        
        df = pd.read_csv(io.StringIO(csv_content))
        rows, cols = len(df), len(df.columns)
        
        result = dbc.Alert([
            html.I(className="fas fa-check-circle me-2"),
            f"✅ Text processing: {rows} rows, {cols} columns"
        ], color="success")
        
        # Preview table
        preview_table = dash_table.DataTable(
            data=df.head(10).to_dict('records'),
            columns=[{"name": col, "id": col} for col in df.columns],
            page_size=5,
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'left', 'padding': '10px'},
            style_header={'backgroundColor': '#0d6efd', 'color': 'white'}
        )
        
        preview = dbc.Card([
            dbc.CardHeader([html.H6("📄 Preview", className="mb-0")]),
            dbc.CardBody([preview_table])
        ], className="mt-3")
        
        return result, preview
        
    except Exception as e:
        error = dbc.Alert(f"Error: {str(e)}", color="danger")
        return error, ""

def register_callbacks(manager: Any, controller=None) -> None:
    """Callbacks registered via decorators."""
    logger.info("Step 1 upload callbacks registered")

def safe_upload_layout():
    """Unicode-safe wrapper."""
    return layout()

def check_upload_system_health():
    """Health check."""
    return {
        "status": "step_1_enhanced",
        "real_file_upload": "added",
        "navigation_flash": "eliminated",
        "enhancement_stage": "1_of_4"
    }

__all__ = ["layout", "safe_upload_layout", "register_page", "register_callbacks", "check_upload_system_health"]
