from flask import Flask, request, jsonify

from utils.api_error import error_response
from flask_cors import CORS
import os
import json
import pandas as pd
import hashlib
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Configure upload
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv', 'xls', 'xlsx'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('mappings', exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_fingerprint(content):
    """Generate a unique fingerprint for file content"""
    return hashlib.md5(content).hexdigest()

@app.route('/v1/upload', methods=['POST'])
def upload_files():
    """Handle file upload with the structure expected by the React frontend"""
    try:
        results = []
        
        # Process each uploaded file
        for file_key in request.files:
            file = request.files[file_key]
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filepath)
                
                # Read file content for fingerprint
                with open(filepath, 'rb') as f:
                    content = f.read()
                fingerprint = get_file_fingerprint(content)
                
                # Analyze file
                try:
                    if filename.endswith('.csv'):
                        df = pd.read_csv(filepath)
                    else:
                        df = pd.read_excel(filepath)
                    
                    columns = df.columns.tolist()
                    rows = len(df)
                    
                    # Prepare file info
                    file_info = {
                        'filename': filename,
                        'fingerprint': fingerprint,
                        'rows': rows,
                        'columns': columns,
                        'size': os.path.getsize(filepath),
                        'uploaded_at': datetime.now().isoformat()
                    }
                    
                    # Check if we have standard columns
                    standard_columns = ['timestamp', 'device_id', 'user_id', 'event_type']
                    has_standard_columns = all(col in columns for col in standard_columns)
                    
                    # Get unique devices if device_id column exists
                    devices = []
                    if 'device_id' in columns:
                        devices = df['device_id'].dropna().unique().tolist()[:20]
                    
                    result = {
                        'success': True,
                        'file_info': file_info,
                        'requires_column_mapping': not has_standard_columns,
                        'requires_device_mapping': len(devices) > 0,
                        'devices': devices,
                        'preview_data': df.head(5).to_dict('records')
                    }
                    
                except Exception as e:
                    result = {
                        'success': False,
                        'error': f'Error processing file: {str(e)}',
                        'file_info': {'filename': filename}
                    }
                
                results.append(result)
        
        return jsonify({
            'status': 'success',
            'results': results,
            'session_id': request.form.get('session_id', 'default-session')
        })
        
    except Exception as e:
        return error_response('server_error', str(e)), 500

@app.route('/v1/upload/process', methods=['POST'])
def process_upload():
    """Process uploaded file with mappings"""
    try:
        data = request.json
        session_id = data.get('session_id')
        file_info = data.get('file_info')
        column_mappings = data.get('column_mappings', {})
        device_mappings = data.get('device_mappings', {})
        
        # Here you would process the file with the mappings
        # For now, just return success
        
        result = {
            'success': True,
            'message': 'File processed successfully',
            'file_id': file_info.get('fingerprint'),
            'rows_processed': file_info.get('rows', 0),
            'column_mappings_applied': len(column_mappings),
            'device_mappings_applied': len(device_mappings)
        }
        
        return jsonify(result)
    
    except Exception as e:
        return error_response('server_error', str(e)), 500

@app.route('/v1/mappings/save', methods=['POST'])
def save_mappings():
    """Save learned mappings for future use"""
    try:
        data = request.json
        learned_mapping = data.get('learned_mapping', {})
        fingerprint = learned_mapping.get('fingerprint', 'unknown')
        
        # Save mapping to file
        mapping_file = os.path.join('mappings', f'{fingerprint}.json')
        with open(mapping_file, 'w') as f:
            json.dump(learned_mapping, f, indent=2)
        
        return jsonify({
            'success': True,
            'message': 'Mappings saved successfully',
            'fingerprint': fingerprint
        })
    
    except Exception as e:
        return error_response('server_error', str(e)), 500

@app.route('/v1/devices', methods=['GET'])
def get_devices():
    """Get list of known devices"""
    # For demo, return some sample devices
    devices = [
        {'id': 'DEV001', 'name': 'Main Entrance', 'floor': 1, 'type': 'entry'},
        {'id': 'DEV002', 'name': 'Emergency Exit', 'floor': 1, 'type': 'exit'},
        {'id': 'DEV003', 'name': 'Elevator Bank A', 'floor': 1, 'type': 'elevator'},
    ]
    return jsonify({'devices': devices})

if __name__ == '__main__':
    app.run(debug=True, port=5001)
