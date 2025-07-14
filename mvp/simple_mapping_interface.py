#!/usr/bin/env python3
"""
Simple Data Mapping Interface
Upload -> View Raw Data -> Column Mapping -> Device Mapping -> Enhanced Data
"""

import os
import sys
import json
import logging
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import base64
import io

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
import dash
from dash import dcc, html, Input, Output, State, callback_context, dash_table
import dash_bootstrap_components as dbc
from flask import Flask

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global data storage for session
session_data = {
    'raw_df': None,
    'enhanced_df': None,
    'filename': None,
    'column_mapping': {},
    'device_mapping': {},
    'ai_suggestions': {},
    'stage': 'upload'
}

def safe_import_column_suggestions():
    """Safely import column suggestion function with fallback"""
    try:
        from services.data_enhancer import get_ai_column_suggestions
        return get_ai_column_suggestions
    except Exception as e:
        logger.warning(f"Could not import get_ai_column_suggestions: {e}")
        
        def fallback_suggestions(columns):
            suggestions = {}
            for col in columns:
                col_lower = col.lower()
                suggestion = {"field": "", "confidence": 0.0}
                
                if any(keyword in col_lower for keyword in ["person", "user", "employee", "name"]):
                    suggestion = {"field": "person_id", "confidence": 0.7}
                elif any(keyword in col_lower for keyword in ["door", "location", "device", "room"]):
                    suggestion = {"field": "door_id", "confidence": 0.7}
                elif any(keyword in col_lower for keyword in ["time", "date", "stamp"]):
                    suggestion = {"field": "timestamp", "confidence": 0.8}
                elif any(keyword in col_lower for keyword in ["result", "status", "access"]):
                    suggestion = {"field": "access_result", "confidence": 0.7}
                elif any(keyword in col_lower for keyword in ["token", "badge", "card"]):
                    suggestion = {"field": "token_id", "confidence": 0.6}
                    
                suggestions[col] = suggestion
            return suggestions
        
        return fallback_suggestions

def safe_import_device_mapping():
    """Safely import device mapping service with fallback"""
    try:
        from services.door_mapping_service import DoorMappingService
        from services.configuration_service import ConfigurationServiceProtocol
        
        class MockConfig:
            def get_ai_confidence_threshold(self):
                return 0.7
        
        return DoorMappingService(MockConfig())
    except Exception as e:
        logger.warning(f"Could not import device mapping service: {e}")
        
        class FallbackDeviceMapping:
            def process_uploaded_data(self, df, client_profile="auto"):
                devices = []
                device_cols = ['door_id', 'device_name', 'DeviceName', 'location', 'door', 'device']
                
                for col in df.columns:
                    if any(device_col.lower() in col.lower() for device_col in device_cols):
                        unique_devices = df[col].dropna().unique()
                        for device in unique_devices:
                            devices.append({
                                'door_id': str(device),
                                'floor_number': 1,
                                'security_level': 5,
                                'is_entry': True,
                                'is_exit': False,
                                'is_elevator': 'elevator' in str(device).lower(),
                                'is_stairwell': 'stair' in str(device).lower(),
                                'is_fire_escape': 'fire' in str(device).lower(),
                                'is_restricted': 'restricted' in str(device).lower(),
                                'confidence': 0.6
                            })
                        break
                
                return {'devices': devices, 'ai_model_version': 'fallback_v1.0'}
        
        return FallbackDeviceMapping()

# Initialize services with fallbacks
get_ai_column_suggestions = safe_import_column_suggestions()
device_mapping_service = safe_import_device_mapping()

def process_file_content(contents, filename):
    """Process uploaded file content with encoding safety"""
    try:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        
        encodings = ['utf-8', 'utf-8-sig', 'latin1', 'cp1252', 'iso-8859-1']
        df = None
        
        for encoding in encodings:
            try:
                if filename.endswith('.csv'):
                    text_content = decoded.decode(encoding, errors='replace')
                    text_content = ''.join(char for char in text_content 
                                         if not (0xD800 <= ord(char) <= 0xDFFF))
                    
                    df = pd.read_csv(io.StringIO(text_content))
                    break
                elif filename.endswith('.json'):
                    text_content = decoded.decode(encoding, errors='replace')
                    text_content = ''.join(char for char in text_content 
                                         if not (0xD800 <= ord(char) <= 0xDFFF))
                    
                    data = json.loads(text_content)
                    if isinstance(data, list):
                        df = pd.DataFrame(data)
                    else:
                        df = pd.DataFrame([data])
                    break
            except Exception:
                continue
        
        if df is None:
            raise ValueError("Could not process file with any encoding")
        
        df.columns = [str(col).strip() for col in df.columns]
        
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].astype(str).apply(
                    lambda x: ''.join(char for char in str(x) 
                                    if not (0xD800 <= ord(char) <= 0xDFFF))
                )
        
        logger.info(f"Successfully processed {filename}: {len(df)} rows, {len(df.columns)} columns")
        return df, None
        
    except Exception as e:
        error_msg = f"Error processing {filename}: {str(e)}"
        logger.error(error_msg)
        return None, error_msg

def enhance_data_with_mappings(df, column_mapping, device_mapping):
    """Enhance data by applying column and device mappings"""
    try:
        enhanced_df = df.copy()
        
        if column_mapping:
            rename_dict = {}
            for original_col, mapped_field in column_mapping.items():
                if mapped_field and mapped_field != "":
                    rename_dict[original_col] = mapped_field
            
            if rename_dict:
                enhanced_df = enhanced_df.rename(columns=rename_dict)
        
        if device_mapping and 'door_id' in enhanced_df.columns:
            device_lookup = {device['door_id']: device for device in device_mapping}
            
            enhanced_df['floor_number'] = enhanced_df['door_id'].map(
                lambda x: device_lookup.get(str(x), {}).get('floor_number', 1)
            )
            enhanced_df['security_level'] = enhanced_df['door_id'].map(
                lambda x: device_lookup.get(str(x), {}).get('security_level', 5)
            )
            enhanced_df['is_entry'] = enhanced_df['door_id'].map(
                lambda x: device_lookup.get(str(x), {}).get('is_entry', False)
            )
            enhanced_df['is_exit'] = enhanced_df['door_id'].map(
                lambda x: device_lookup.get(str(x), {}).get('is_exit', False)
            )
            enhanced_df['is_elevator'] = enhanced_df['door_id'].map(
                lambda x: device_lookup.get(str(x), {}).get('is_elevator', False)
            )
            enhanced_df['is_restricted'] = enhanced_df['door_id'].map(
                lambda x: device_lookup.get(str(x), {}).get('is_restricted', False)
            )
        
        return enhanced_df, None
        
    except Exception as e:
        error_msg = f"Error enhancing data: {str(e)}"
        logger.error(error_msg)
        return df, error_msg

server = Flask(__name__)
app = dash.Dash(__name__, server=server, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.config.suppress_callback_exceptions = True
app.config.suppress_callback_exceptions = True

def create_upload_stage():
    return [
        dbc.Row([
            dbc.Col([
                html.H3("📂 Step 1: Upload CSV/JSON File", className="mb-3"),
                dcc.Upload(
                    id='upload-data',
                    children=html.Div([
                        'Drag and Drop or ',
                        html.A('Select Files')
                    ]),
                    style={
                        'width': '100%',
                        'height': '200px',
                        'lineHeight': '200px',
                        'borderWidth': '2px',
                        'borderStyle': 'dashed',
                        'borderRadius': '10px',
                        'textAlign': 'center',
                        'margin': '10px',
                        'backgroundColor': '#f8f9fa'
                    },
                    multiple=False
                ),
            ], width=12)
        ])
    ]

app.layout = dbc.Container([
    dcc.Store(id='session-store', data=session_data),
    dbc.Row([
        dbc.Col([
            html.H1("🔧 Simple Data Mapping Interface", className="text-center mb-4"),
            html.Hr()
        ])
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Progress(id="progress-bar", value=0, max=5, striped=True, animated=True, 
                        color="primary", className="mb-4")
        ])
    ]),
    html.Div(id="main-content", children=create_upload_stage()),
    html.Div(id="status-messages"),
    dcc.Store(id='file-data-store'),
    dcc.Store(id='column-mapping-store'),
    dcc.Store(id='device-mapping-store'),
], fluid=True)

def create_raw_data_stage(df):
    if df is None or len(df) == 0:
        return [html.Div("No data to display")]
    
    display_df = df.head(5)
    
    return [
        dbc.Row([
            dbc.Col([
                html.H3("📊 Step 2: Raw Data Preview (First 5 Rows)", className="mb-3"),
                html.P(f"Total rows: {len(df)}, Columns: {len(df.columns)}"),
                dash_table.DataTable(
                    data=display_df.to_dict('records'),
                    columns=[{"name": str(col), "id": str(col)} for col in display_df.columns],
                    style_table={'overflowX': 'auto'},
                    style_cell={'textAlign': 'left', 'padding': '10px'},
                    style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},
                    page_size=5
                ),
                html.Br(),
                dbc.Button("Next: Column Mapping", id="btn-to-column-mapping", 
                          color="primary", size="lg", className="mt-3")
            ], width=12)
        ])
    ]

def create_column_mapping_stage(df):
    if df is None:
        return [html.Div("No data available")]
    
    ai_suggestions = get_ai_column_suggestions(df.columns)
    
    standard_fields = [
        {"label": "Not Mapped", "value": ""},
        {"label": "Person ID", "value": "person_id"},
        {"label": "Door/Device ID", "value": "door_id"},
        {"label": "Access Result", "value": "access_result"},
        {"label": "Timestamp", "value": "timestamp"},
        {"label": "Token/Badge ID", "value": "token_id"},
        {"label": "Event Type", "value": "event_type"},
    ]
    
    column_cards = []
    for col in df.columns:
        ai_suggestion = ai_suggestions.get(col, {})
        suggested_field = ai_suggestion.get("field", "")
        confidence = ai_suggestion.get("confidence", 0.0)
        
        card = dbc.Card([
            dbc.CardBody([
                html.H6(f"Column: {col}", className="card-title"),
                html.P(f"AI Suggestion: {suggested_field} ({confidence:.1%} confidence)" if suggested_field else "No AI suggestion"),
                dbc.Label("Map to:"),
                dcc.Dropdown(
                    id={"type": "column-mapping", "index": col},
                    options=standard_fields,
                    value=suggested_field,
                    placeholder="Select mapping..."
                )
            ])
        ], className="mb-2")
        column_cards.append(card)
    
    return [
        dbc.Row([
            dbc.Col([
                html.H3("🎯 Step 3: Column Mapping (AI + Manual)", className="mb-3"),
                html.P("Map your data columns to standard fields. AI suggestions are pre-filled."),
                html.Div(column_cards),
                html.Br(),
                dbc.ButtonGroup([
                    dbc.Button("Back to Raw Data", id="btn-back-to-raw", color="secondary"),
                    dbc.Button("Apply AI Suggestions", id="btn-apply-ai-suggestions", color="info"),
                    dbc.Button("Next: Device Mapping", id="btn-to-device-mapping", color="primary")
                ], className="mt-3")
            ], width=12)
        ])
    ]

def create_device_mapping_stage(df, column_mapping):
    if df is None:
        return [html.Div("No data available")]
    
    enhanced_df = df.copy()
    if column_mapping:
        rename_dict = {k: v for k, v in column_mapping.items() if v}
        enhanced_df = enhanced_df.rename(columns=rename_dict)
    
    devices = []
    device_cols = ['door_id', 'device_name', 'DeviceName', 'location', 'door', 'device']
    
    for col in enhanced_df.columns:
        if col in device_cols or any(dc.lower() in col.lower() for dc in device_cols):
            devices = enhanced_df[col].dropna().unique()
            break
    
    if len(devices) == 0:
        return [html.Div("No devices found. Please check column mapping.")]
    
    try:
        ai_device_result = device_mapping_service.process_uploaded_data(enhanced_df)
        ai_devices = {d['door_id']: d for d in ai_device_result.get('devices', [])}
    except Exception as e:
        logger.warning(f"AI device mapping failed: {e}")
        ai_devices = {}
    
    device_cards = []
    for device in devices[:10]:
        device_str = str(device)
        ai_data = ai_devices.get(device_str, {})
        
        card = dbc.Card([
            dbc.CardBody([
                html.H6(f"Device: {device_str}", className="card-title"),
                html.P(f"AI Confidence: {ai_data.get('confidence', 0):.1%}" if ai_data else "No AI data"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Floor Number:"),
                        dbc.Input(
                            id={"type": "device-floor", "index": device_str},
                            type="number",
                            value=ai_data.get('floor_number', 1),
                            min=1, max=50
                        )
                    ], width=6),
                    dbc.Col([
                        dbc.Label("Security Level (1-10):"),
                        dbc.Input(
                            id={"type": "device-security", "index": device_str},
                            type="number",
                            value=ai_data.get('security_level', 5),
                            min=1, max=10
                        )
                    ], width=6)
                ]),
                
                html.Br(),
                
                dbc.Label("Access Type:"),
                dcc.Checklist(
                    id={"type": "device-access", "index": device_str},
                    options=[
                        {"label": "Entry Point", "value": "is_entry"},
                        {"label": "Exit Point", "value": "is_exit"}
                    ],
                    value=[k for k, v in ai_data.items() if k in ['is_entry', 'is_exit'] and v],
                    inline=True
                ),
                
                html.Br(),
                
                dbc.Label("Special Properties:"),
                dcc.Checklist(
                    id={"type": "device-special", "index": device_str},
                    options=[
                        {"label": "Elevator", "value": "is_elevator"},
                        {"label": "Stairwell", "value": "is_stairwell"},
                        {"label": "Fire Exit", "value": "is_fire_escape"},
                        {"label": "Restricted", "value": "is_restricted"}
                    ],
                    value=[k for k, v in ai_data.items() if k in ['is_elevator', 'is_stairwell', 'is_fire_escape', 'is_restricted'] and v],
                    inline=True
                )
            ])
        ], className="mb-3")
        device_cards.append(card)
    
    return [
        dbc.Row([
            dbc.Col([
                html.H3("🏢 Step 4: Device Mapping (AI + Manual)", className="mb-3"),
                html.P(f"Configure properties for {len(devices)} devices. AI suggestions are pre-filled."),
                html.Div(device_cards),
                html.Br(),
                dbc.ButtonGroup([
                    dbc.Button("Back to Column Mapping", id="btn-back-to-column", color="secondary"),
                    dbc.Button("Apply AI Device Mapping", id="btn-apply-ai-devices", color="info"),
                    dbc.Button("Next: Enhanced Data", id="btn-to-enhanced", color="primary")
                ], className="mt-3")
            ], width=12)
        ])
    ]

def create_enhanced_data_stage(enhanced_df, original_df):
    if enhanced_df is None:
        return [html.Div("No enhanced data available")]
    
    display_df = enhanced_df.head(5)
    
    original_cols = len(original_df.columns) if original_df is not None else 0
    enhanced_cols = len(enhanced_df.columns)
    new_cols = enhanced_cols - original_cols
    
    return [
        dbc.Row([
            dbc.Col([
                html.H3("✨ Step 5: Enhanced Data Preview (First 5 Rows)", className="mb-3"),
                
                dbc.Alert([
                    html.H5("Enhancement Summary:", className="alert-heading"),
                    html.P(f"Original columns: {original_cols}"),
                    html.P(f"Enhanced columns: {enhanced_cols}"),
                    html.P(f"New columns added: {new_cols}")
                ], color="success"),
                
                dash_table.DataTable(
                    data=display_df.to_dict('records'),
                    columns=[{"name": str(col), "id": str(col)} for col in display_df.columns],
                    style_table={'overflowX': 'auto'},
                    style_cell={'textAlign': 'left', 'padding': '8px', 'fontSize': '12px'},
                    style_header={'backgroundColor': 'rgb(40, 167, 69)', 'color': 'white', 'fontWeight': 'bold'},
                    style_data_conditional=[
                        {
                            'if': {'column_id': col},
                            'backgroundColor': 'rgb(248, 255, 248)',
                            'border': '1px solid rgb(40, 167, 69)'
                        } for col in display_df.columns if col not in (original_df.columns if original_df is not None else [])
                    ],
                    page_size=5
                ),
                
                html.Br(),
                
                dbc.ButtonGroup([
                    dbc.Button("Back to Device Mapping", id="btn-back-to-device", color="secondary"),
                    dbc.Button("Download Enhanced Data", id="btn-download-enhanced", color="success"),
                    dbc.Button("Start New Upload", id="btn-new-upload", color="primary")
                ], className="mt-3")
            ], width=12)
        ])
    ]

@app.callback(
    [Output("main-content", "children"),
     Output("progress-bar", "value"),
     Output("session-store", "data"),
     Output("status-messages", "children")],
    [Input("upload-data", "contents"),
     Input("btn-to-column-mapping", "n_clicks"),
     Input("btn-to-device-mapping", "n_clicks"),
     Input("btn-to-enhanced", "n_clicks"),
     Input("btn-back-to-raw", "n_clicks"),
     Input("btn-back-to-column", "n_clicks"),
     Input("btn-back-to-device", "n_clicks"),
     Input("btn-new-upload", "n_clicks")],
    [State("upload-data", "filename"),
     State("session-store", "data")]
)
def update_main_content(contents, btn_column, btn_device, btn_enhanced, 
                       btn_back_raw, btn_back_column, btn_back_device, btn_new,
                       filename, stored_data):
    
    ctx = callback_context
    if not ctx.triggered:
        return create_upload_stage(), 0, stored_data, ""
    
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    status_msg = ""
    
    if trigger_id == "upload-data" and contents is not None:
        df, error = process_file_content(contents, filename)
        if error:
            return create_upload_stage(), 0, stored_data, dbc.Alert(error, color="danger")
        
        stored_data.update({
            'raw_df': df.to_dict('records'),
            'filename': filename,
            'stage': 'raw_view'
        })
        return create_raw_data_stage(df), 1, stored_data, dbc.Alert(f"Successfully loaded {filename}", color="success")
    
    elif trigger_id == "btn-to-column-mapping":
        if stored_data.get('raw_df'):
            df = pd.DataFrame(stored_data['raw_df'])
            stored_data['stage'] = 'column_mapping'
            return create_column_mapping_stage(df), 2, stored_data, ""
    
    elif trigger_id == "btn-to-device-mapping":
        if stored_data.get('raw_df'):
            df = pd.DataFrame(stored_data['raw_df'])
            column_mapping = stored_data.get('column_mapping', {})
            stored_data['stage'] = 'device_mapping'
            return create_device_mapping_stage(df, column_mapping), 3, stored_data, ""
    
    elif trigger_id == "btn-to-enhanced":
        if stored_data.get('raw_df'):
            df = pd.DataFrame(stored_data['raw_df'])
            column_mapping = stored_data.get('column_mapping', {})
            device_mapping = stored_data.get('device_mapping', [])
            
            enhanced_df, error = enhance_data_with_mappings(df, column_mapping, device_mapping)
            if error:
                return dash.no_update, dash.no_update, stored_data, dbc.Alert(error, color="danger")
            
            stored_data.update({
                'enhanced_df': enhanced_df.to_dict('records'),
                'stage': 'enhanced_view'
            })
            return create_enhanced_data_stage(enhanced_df, df), 5, stored_data, ""
    
    elif trigger_id == "btn-back-to-raw":
        if stored_data.get('raw_df'):
            df = pd.DataFrame(stored_data['raw_df'])
            stored_data['stage'] = 'raw_view'
            return create_raw_data_stage(df), 1, stored_data, ""
    
    elif trigger_id == "btn-back-to-column":
        if stored_data.get('raw_df'):
            df = pd.DataFrame(stored_data['raw_df'])
            stored_data['stage'] = 'column_mapping'
            return create_column_mapping_stage(df), 2, stored_data, ""
    
    elif trigger_id == "btn-back-to-device":
        if stored_data.get('raw_df'):
            df = pd.DataFrame(stored_data['raw_df'])
            column_mapping = stored_data.get('column_mapping', {})
            stored_data['stage'] = 'device_mapping'
            return create_device_mapping_stage(df, column_mapping), 3, stored_data, ""
    
    elif trigger_id == "btn-new-upload":
        stored_data = {
            'raw_df': None,
            'enhanced_df': None,
            'filename': None,
            'column_mapping': {},
            'device_mapping': {},
            'ai_suggestions': {},
            'stage': 'upload'
        }
        return create_upload_stage(), 0, stored_data, ""
    
    return dash.no_update, dash.no_update, stored_data, status_msg

@app.callback(
    Output("session-store", "data", allow_duplicate=True),
    [Input({"type": "column-mapping", "index": dash.dependencies.ALL}, "value")],
    [State({"type": "column-mapping", "index": dash.dependencies.ALL}, "id"),
     State("session-store", "data")],
    prevent_initial_call=True
)
def update_column_mapping(values, ids, stored_data):
    if not values or not ids:
        return stored_data
    
    column_mapping = {}
    for i, value in enumerate(values):
        if value:
            column_name = ids[i]["index"]
            column_mapping[column_name] = value
    
    stored_data['column_mapping'] = column_mapping
    return stored_data

@app.callback(
    Output("session-store", "data", allow_duplicate=True),
    [Input({"type": "device-floor", "index": dash.dependencies.ALL}, "value"),
     Input({"type": "device-security", "index": dash.dependencies.ALL}, "value"),
     Input({"type": "device-access", "index": dash.dependencies.ALL}, "value"),
     Input({"type": "device-special", "index": dash.dependencies.ALL}, "value")],
    [State({"type": "device-floor", "index": dash.dependencies.ALL}, "id"),
     State("session-store", "data")],
    prevent_initial_call=True
)
def update_device_mapping(floors, security_levels, access_types, special_props, ids, stored_data):
    if not ids:
        return stored_data
    
    device_mapping = []
    for i, device_id in enumerate([id_dict["index"] for id_dict in ids]):
        device_data = {
            'door_id': device_id,
            'floor_number': floors[i] if i < len(floors) and floors[i] is not None else 1,
            'security_level': security_levels[i] if i < len(security_levels) and security_levels[i] is not None else 5,
            'is_entry': 'is_entry' in (access_types[i] if i < len(access_types) and access_types[i] else []),
            'is_exit': 'is_exit' in (access_types[i] if i < len(access_types) and access_types[i] else []),
            'is_elevator': 'is_elevator' in (special_props[i] if i < len(special_props) and special_props[i] else []),
            'is_stairwell': 'is_stairwell' in (special_props[i] if i < len(special_props) and special_props[i] else []),
            'is_fire_escape': 'is_fire_escape' in (special_props[i] if i < len(special_props) and special_props[i] else []),
            'is_restricted': 'is_restricted' in (special_props[i] if i < len(special_props) and special_props[i] else [])
        }
        device_mapping.append(device_data)
    
    stored_data['device_mapping'] = device_mapping
    return stored_data

if __name__ == "__main__":
    print("🚀 Starting Simple Data Mapping Interface...")
    print("📊 Features:")
    print("  • CSV/JSON file upload with Unicode safety")
    print("  • Raw data preview (first 5 rows)")
    print("  • AI + Manual column mapping")
    print("  • AI + Manual device mapping")
    print("  • Enhanced data visualization")
    print("  • Modular, testable code structure")
    print("\n🌐 Open: http://localhost:5002")
    print("🔄 Ready for file upload and mapping...")
    
    app.run_server(debug=True, host="0.0.0.0", port=5002)
