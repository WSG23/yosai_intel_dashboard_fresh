#!/usr/bin/env python3
"""
Minimal Flask API for React Upload component
Bypasses circular imports by using services directly
"""
from flask import Flask, request, jsonify

from utils.api_error import error_response
from flask_cors import CORS
import pandas as pd
import asyncio
import json
import sys
from pathlib import Path
from config.constants import API_PORT

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

app = Flask(__name__)
CORS(app)

# Global storage for uploaded data
uploaded_data = {}

@app.route('/v1/upload', methods=['POST'])
def upload_files():
    """Handle file upload and return expected structure"""
    try:
        # Support both multipart/form-data and JSON payloads
        if 'file' in request.files:
            file = request.files['file']
            if not file.filename:
                return error_response('no_file_selected', 'No file selected'), 400

            filename = file.filename
            file_bytes = file.read()
        else:
            data = request.get_json(silent=True)
            if not data:
                return error_response('no_data', 'No data provided'), 400

            contents = data.get('contents', [])
            filenames = data.get('filenames', [])

            if not contents or not filenames:
                return error_response('no_files', 'No files provided'), 400

            content = contents[0]
            filename = filenames[0]

            import base64
            if ',' in content:
                content = content.split(',')[1]
            file_bytes = base64.b64decode(content)

        import io
        
        # Read into pandas based on file type
        if filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(file_bytes))
        elif filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(file_bytes))
        elif filename.endswith('.json'):
            df = pd.read_json(io.BytesIO(file_bytes))
        else:
            return error_response('unsupported_type', 'Unsupported file type'), 400
        
        # Store dataframe
        uploaded_data[filename] = df
        
        # Get AI column suggestions
        from services.data_enhancer import get_ai_column_suggestions
        ai_suggestions = {}
        try:
            ai_suggestions = get_ai_column_suggestions(df)
        except:
            # Fallback to simple suggestions
            ai_suggestions = create_simple_suggestions(df)
        
        # Build response
        response = {
            'upload_results': [{'status': 'success', 'filename': filename}],
            'file_preview_components': [],
            'file_info_dict': {
                filename: {
                    'filename': filename,
                    'rows': len(df),
                    'columns': len(df.columns),
                    'ai_suggestions': ai_suggestions,
                    'column_names': df.columns.tolist()
                }
            }
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        print(f"Upload error: {e}")
        return error_response('server_error', str(e)), 500

@app.route('/v1/ai/suggest-devices', methods=['POST'])
def suggest_devices():
    """Get device suggestions"""
    try:
        data = request.json
        filename = data.get('filename')
        column_mappings = data.get('column_mappings', {})
        
        # Get dataframe
        df = uploaded_data.get(filename)
        if df is None:
            return error_response('not_found', 'File not found'), 404
        
        # Find device column
        devices = []
        device_column = None
        
        for source_col, mapped_col in column_mappings.items():
            if mapped_col in ['device_name', 'device', 'hostname']:
                device_column = source_col
                break
        
        if device_column and device_column in df.columns:
            devices = df[device_column].dropna().unique().tolist()
        
        # Create device mappings
        device_mappings = {}
        
        # Try to use DeviceLearningService if available
        try:
            from services.device_learning_service import DeviceLearningService
            device_service = DeviceLearningService()
            
            # Check for saved mappings
            user_mappings = device_service.get_user_device_mappings(filename)
            
            if user_mappings:
                for device, mapping in user_mappings.items():
                    device_mappings[device] = {
                        'device_type': mapping.get('device_type', 'unknown'),
                        'location': mapping.get('location'),
                        'properties': mapping.get('properties', {}),
                        'confidence': 1.0,
                        'source': 'user_confirmed'
                    }
            else:
                # Generate AI suggestions
                device_mappings = create_device_suggestions(devices)
        except:
            # Fallback to simple suggestions
            device_mappings = create_device_suggestions(devices)
        
        return jsonify({
            'devices': devices,
            'device_mappings': device_mappings
        }), 200
        
    except Exception as e:
        print(f"Device suggestion error: {e}")
        return error_response('server_error', str(e)), 500

@app.route('/v1/mappings/save', methods=['POST'])
def save_mappings():
    """Save mappings"""
    try:
        data = request.json
        filename = data.get('filename')
        mapping_type = data.get('mapping_type')
        
        # For now, just return success
        # In production, save to database or file
        
        return jsonify({'status': 'success'}), 200
        
    except Exception as e:
        return error_response('server_error', str(e)), 500

@app.route('/v1/process-enhanced', methods=['POST'])
def process_enhanced_data():
    """Process data with mappings"""
    try:
        data = request.json
        filename = data.get('filename')
        column_mappings = data.get('column_mappings', {})
        device_mappings = data.get('device_mappings', {})
        
        # Get dataframe
        df = uploaded_data.get(filename)
        if df is None:
            return error_response('not_found', 'File not found'), 404
        
        # Apply column mappings
        if column_mappings:
            df = df.rename(columns=column_mappings)
        
        # Apply device mappings
        if device_mappings and 'device_name' in df.columns:
            df['device_type'] = df['device_name'].map(
                lambda x: device_mappings.get(x, {}).get('device_type', 'unknown')
            )
            df['location'] = df['device_name'].map(
                lambda x: device_mappings.get(x, {}).get('location', '')
            )
        
        # Store enhanced data
        enhanced_filename = f"enhanced_{filename}"
        uploaded_data[enhanced_filename] = df
        
        return jsonify({
            'status': 'success',
            'enhanced_filename': enhanced_filename,
            'rows': len(df),
            'columns': len(df.columns)
        }), 200
        
    except Exception as e:
        return error_response('server_error', str(e)), 500

# Helper functions for fallback suggestions
def create_simple_suggestions(df):
    """Create simple column suggestions based on column names"""
    suggestions = {}
    
    # Common patterns
    patterns = {
        'timestamp': ['time', 'date', 'datetime', 'ts', 'created', 'updated'],
        'source': ['src', 'source', 'from', 'origin', 'sender'],
        'destination': ['dst', 'dest', 'to', 'target', 'receiver'],
        'port': ['port', 'dst_port', 'src_port'],
        'protocol': ['proto', 'protocol'],
        'device_name': ['device', 'host', 'hostname', 'name', 'machine'],
        'user': ['user', 'username', 'account', 'login'],
        'action': ['action', 'event', 'status', 'result']
    }
    
    for col in df.columns:
        col_lower = col.lower()
        for field, keywords in patterns.items():
            if any(keyword in col_lower for keyword in keywords):
                suggestions[col] = {
                    'field': field,
                    'confidence': 0.8,
                    'reasoning': f"Column name '{col}' matches pattern for {field}"
                }
                break
    
    return suggestions

def create_device_suggestions(devices):
    """Create simple device type suggestions"""
    device_mappings = {}
    
    # Common device patterns
    patterns = {
        'firewall': ['fw', 'firewall', 'asa', 'palo'],
        'router': ['rtr', 'router', 'gw', 'gateway'],
        'switch': ['sw', 'switch'],
        'server': ['srv', 'server', 'dc'],
        'workstation': ['ws', 'workstation', 'desktop', 'pc'],
        'printer': ['prn', 'printer', 'print'],
        'camera': ['cam', 'camera', 'ipcam']
    }
    
    for device in devices:
        device_lower = str(device).lower()
        device_type = 'unknown'
        confidence = 0.5
        
        # Check patterns
        for dtype, keywords in patterns.items():
            if any(keyword in device_lower for keyword in keywords):
                device_type = dtype
                confidence = 0.8
                break
        
        device_mappings[device] = {
            'device_type': device_type,
            'location': '',
            'properties': {},
            'confidence': confidence,
            'source': 'ai_suggested'
        }
    
    return device_mappings

if __name__ == '__main__':
    print("Starting minimal Flask API server...")
    print(f"Server running on http://localhost:{API_PORT}")
    print("Endpoints:")
    print("  POST /v1/upload")
    print("  POST /v1/ai/suggest-devices")
    print("  POST /v1/mappings/save")
    print("  POST /v1/process-enhanced")
    app.run(host='0.0.0.0', port=API_PORT, debug=True)
