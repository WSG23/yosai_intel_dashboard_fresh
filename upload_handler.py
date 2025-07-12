#!/usr/bin/env python3
"""
Direct Flask file upload handler - bypasses Dash complexity
"""
import os
import pandas as pd
from flask import Flask, request, jsonify, render_template_string
from werkzeug.utils import secure_filename
import uuid

# Global storage for uploaded files
UPLOADED_FILES = {}
UPLOAD_FOLDER = 'temp_uploads'

# Create upload directory
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def create_upload_app():
    """Create Flask app with file upload endpoint"""
    app = Flask(__name__)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max
    
    @app.route('/upload', methods=['GET', 'POST'])
    def upload_file():
        if request.method == 'GET':
            return render_template_string(UPLOAD_HTML)
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file:
            # Secure filename and save
            filename = secure_filename(file.filename)
            unique_id = str(uuid.uuid4())[:8]
            safe_filename = f"{unique_id}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
            file.save(filepath)
            
            # Process file immediately
            try:
                df = process_uploaded_file(filepath, filename)
                file_info = {
                    'id': unique_id,
                    'original_name': filename,
                    'filepath': filepath,
                    'dataframe': df,
                    'rows': len(df),
                    'columns': len(df.columns),
                    'preview': df.head(5).to_dict('records')
                }
                
                # Store globally for Dash to access
                UPLOADED_FILES[unique_id] = file_info
                
                return jsonify({
                    'success': True,
                    'file_id': unique_id,
                    'filename': filename,
                    'rows': len(df),
                    'columns': len(df.columns),
                    'preview': file_info['preview']
                })
                
            except Exception as e:
                os.remove(filepath)  # Clean up on error
                return jsonify({'error': f'Processing failed: {str(e)}'}), 400
    
    @app.route('/files', methods=['GET'])
    def list_files():
        """Get list of uploaded files"""
        files = []
        for file_id, info in UPLOADED_FILES.items():
            files.append({
                'id': file_id,
                'name': info['original_name'],
                'rows': info['rows'],
                'columns': info['columns']
            })
        return jsonify({'files': files})
    
    @app.route('/file/<file_id>', methods=['GET'])
    def get_file_data(file_id):
        """Get specific file data"""
        if file_id in UPLOADED_FILES:
            info = UPLOADED_FILES[file_id]
            return jsonify({
                'id': file_id,
                'name': info['original_name'],
                'rows': info['rows'],
                'columns': info['columns'],
                'preview': info['preview']
            })
        return jsonify({'error': 'File not found'}), 404
    
    return app

def process_uploaded_file(filepath, original_filename):
    """Process uploaded file - YOUR PROCESSING LOGIC HERE"""
    
    # Read file based on extension
    if original_filename.endswith('.csv'):
        df = pd.read_csv(filepath)
    elif original_filename.endswith(('.xlsx', '.xls')):
        df = pd.read_excel(filepath)
    elif original_filename.endswith('.json'):
        df = pd.read_json(filepath)
    else:
        raise ValueError(f"Unsupported file type: {original_filename}")
    
    # YOUR CUSTOM PROCESSING HERE
    # Add any data cleaning, validation, transformation
    print(f"✅ Processed {original_filename}: {len(df)} rows, {len(df.columns)} columns")
    
    return df

def get_uploaded_files_simple():
    """Get uploaded files for Dash to use"""
    return {info['original_name']: info['dataframe'] for info in UPLOADED_FILES.values()}

# Simple HTML upload interface
UPLOAD_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>File Upload</title>
    <style>
        .upload-area {
            border: 2px dashed #ccc;
            border-radius: 10px;
            width: 480px;
            height: 200px;
            text-align: center;
            padding: 20px;
            margin: 20px auto;
            cursor: pointer;
        }
        .upload-area:hover { border-color: #007bff; }
        .file-info { margin: 20px; padding: 10px; background: #f8f9fa; }
        .success { color: green; }
        .error { color: red; }
    </style>
</head>
<body>
    <h2>📁 File Upload & Processing</h2>
    
    <div class="upload-area" onclick="document.getElementById('file-input').click()">
        <h3>Click to Upload File</h3>
        <p>Supports: CSV, Excel, JSON</p>
        <input type="file" id="file-input" style="display:none" accept=".csv,.xlsx,.xls,.json">
    </div>
    
    <div id="result"></div>
    
    <div id="files-list">
        <h3>📋 Uploaded Files:</h3>
        <div id="files-container"></div>
    </div>
    
    <script>
        document.getElementById('file-input').addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (!file) return;
            
            const formData = new FormData();
            formData.append('file', file);
            
            document.getElementById('result').innerHTML = '⏳ Processing...';
            
            fetch('/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('result').innerHTML = 
                        `<div class="success file-info">
                            ✅ <strong>${data.filename}</strong> uploaded successfully!<br>
                            📊 ${data.rows} rows × ${data.columns} columns<br>
                            🔗 File ID: ${data.file_id}
                        </div>`;
                    loadFilesList();
                } else {
                    document.getElementById('result').innerHTML = 
                        `<div class="error file-info">❌ ${data.error}</div>`;
                }
            })
            .catch(error => {
                document.getElementById('result').innerHTML = 
                    `<div class="error file-info">❌ Upload failed: ${error}</div>`;
            });
        });
        
        function loadFilesList() {
            fetch('/files')
            .then(response => response.json())
            .then(data => {
                const container = document.getElementById('files-container');
                container.innerHTML = data.files.map(file => 
                    `<div class="file-info">
                        📁 <strong>${file.name}</strong> (${file.rows} rows × ${file.columns} cols)
                        <button onclick="window.open('/analytics', '_blank')">🔗 Analyze</button>
                    </div>`
                ).join('');
            });
        }
        
        // Load files on page load
        loadFilesList();
    </script>
</body>
</html>
'''

if __name__ == "__main__":
    app = create_upload_app()
    print("🚀 Starting file upload server...")
    print("📁 Upload at: http://localhost:5001/upload")
    print("📋 Files API: http://localhost:5001/files")
    app.run(debug=True, port=5001)
