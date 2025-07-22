#!/usr/bin/env python3
import os
from flask import Flask, jsonify, request, send_from_directory

from utils.api_error import error_response
from flask_cors import CORS
from werkzeug.utils import secure_filename
import pandas as pd
import json
from datetime import datetime

# Create Flask app
app = Flask(__name__, static_folder='../build', static_url_path='')
CORS(app, origins=["http://localhost:3000", "http://localhost:3001"])

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def safe_json_dumps(obj):
    """Safely serialize object to JSON, handling Unicode surrogates"""
    def clean_string(s):
        if isinstance(s, str):
            # Remove Unicode surrogates
            return s.encode('utf-8', 'surrogatepass').decode('utf-8', 'replace')
        return s
    
    def clean_dict(d):
        if isinstance(d, dict):
            return {k: clean_dict(v) for k, v in d.items()}
        elif isinstance(d, list):
            return [clean_dict(i) for i in d]
        elif isinstance(d, str):
            return clean_string(d)
        return d
    
    return json.dumps(clean_dict(obj))

@app.route('/v1/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/v1/upload', methods=['POST'])
def upload_file():
    """Handle file upload and return column preview"""
    try:
        if 'file' not in request.files:
            return error_response('no_file', 'No file provided'), 400
        
        file = request.files['file']
        if file.filename == '':
            return error_response('no_file_selected', 'No file selected'), 400
        
        if not allowed_file(file.filename):
            return error_response('invalid_type', 'Invalid file type'), 400
        
        # Save file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Read file and get preview
        try:
            if filename.endswith('.csv'):
                df = pd.read_csv(filepath, nrows=10)
            else:
                df = pd.read_excel(filepath, nrows=10)
            
            # Get column info
            columns = [{'name': col, 'type': str(df[col].dtype)} for col in df.columns]
            
            # Convert preview data
            preview_data = df.head(5).fillna('').to_dict('records')
            
            response_data = {
                'fileId': filename,
                'columns': columns,
                'preview': preview_data,
                'totalRows': len(df)
            }
            
            return jsonify(response_data), 200
            
        except Exception as e:
            os.remove(filepath)  # Clean up on error
            return error_response('read_error', f'Failed to read file: {str(e)}'), 400
            
    except Exception as e:
        return error_response('server_error', str(e)), 500

@app.route('/v1/process', methods=['POST'])
def process_file():
    """Process uploaded file with column mappings"""
    try:
        data = request.get_json()
        file_id = data.get('fileId')
        column_mappings = data.get('columnMappings', {})
        device_mappings = data.get('deviceMappings', {})
        
        if not file_id:
            return error_response('no_file_id', 'No fileId provided'), 400
        
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file_id)
        if not os.path.exists(filepath):
            return error_response('not_found', 'File not found'), 404
        
        # Read full file
        if file_id.endswith('.csv'):
            df = pd.read_csv(filepath)
        else:
            df = pd.read_excel(filepath)
        
        # Apply column mappings
        rename_dict = {v: k for k, v in column_mappings.items() if v}
        df = df.rename(columns=rename_dict)
        
        # Process data (placeholder for actual processing logic)
        processed_rows = len(df)
        
        # Clean up uploaded file
        os.remove(filepath)
        
        return jsonify({
            'success': True,
            'processedRows': processed_rows,
            'message': f'Successfully processed {processed_rows} rows'
        }), 200
        
    except Exception as e:
        return error_response('server_error', str(e)), 500

@app.route('/v1/devices', methods=['GET'])
def get_devices():
    """Get list of available devices"""
    # Mock device data - replace with actual database query
    devices = [
        {'id': 'dev1', 'name': 'Device 1', 'type': 'Type A'},
        {'id': 'dev2', 'name': 'Device 2', 'type': 'Type B'},
        {'id': 'dev3', 'name': 'Device 3', 'type': 'Type A'},
    ]
    return jsonify({'devices': devices}), 200

# Serve React app
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    print("Starting Flask server on port 5001...")
    app.run(debug=True, port=5001, host='0.0.0.0')
