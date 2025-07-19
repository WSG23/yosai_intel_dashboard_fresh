from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

# Configure upload
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv', 'xls', 'xlsx'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            
            # Determine if mapping is required based on file type
            file_ext = filename.rsplit('.', 1)[1].lower()
            requires_mapping = file_ext in ['csv', 'xls', 'xlsx']
            
            return jsonify({
                'success': True,
                'filename': filename,
                'filepath': filepath,
                'requiresColumnMapping': requires_mapping,
                'requiresDeviceMapping': False  # Implement logic as needed
            })
        
        return jsonify({'error': 'File type not allowed'}), 400
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload/process', methods=['POST'])
def process_upload():
    try:
        session_id = request.form.get('session_id')
        file_info = json.loads(request.form.get('file_info'))
        
        if 'file' in request.files:
            file = request.files['file']
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
        
        # Process file (implement your logic)
        result = {
            'success': True,
            'message': 'File processed successfully',
            'file_id': file_info.get('fingerprint'),
            'rows_processed': file_info.get('rows', 0)
        }
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/mappings/save', methods=['POST'])
def save_mappings():
    try:
        data = request.json
        session_id = data.get('session_id')
        learned_mapping = data.get('learned_mapping')
        
        # Save to database or file
        mapping_file = f"mappings/{learned_mapping['fingerprint']}.json"
        os.makedirs('mappings', exist_ok=True)
        
        with open(mapping_file, 'w') as f:
            json.dump(learned_mapping, f)
        
        return jsonify({'success': True})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8050)
