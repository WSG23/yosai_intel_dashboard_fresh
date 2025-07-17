from flask import Flask, jsonify, request, Blueprint
from flask_cors import CORS
from analytics_endpoints import register_analytics_blueprints
import logging
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)

def safe_json_response(data, status=200):
    """Safely encode response data, handling Unicode surrogate characters"""
    try:
        response_data = json.dumps(data, ensure_ascii=False)
        return jsonify(json.loads(response_data)), status
    except UnicodeDecodeError:
        cleaned_data = json.dumps(data, ensure_ascii=True, errors='replace')
        return jsonify(json.loads(cleaned_data)), status

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["http://localhost:3000", "http://localhost:3001", "http://localhost:3002"]}})

# Create API blueprint
api_bp = Blueprint("api_v1", __name__, url_prefix="/api/v1")

# Register analytics blueprints
register_analytics_blueprints(app)

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@api_bp.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload"""
    try:
        if 'file' not in request.files:
            return safe_json_response({'error': 'No file provided'}, 400)
        
        file = request.files['file']
        if file.filename == '':
            return safe_json_response({'error': 'No file selected'}, 400)
        
        # Mock response for now
        return safe_json_response({
            'success': True,
            'columns': ['timestamp', 'source_ip', 'dest_ip', 'action', 'protocol'],
            'detected_devices': ['192.168.1.1', '10.0.0.1', 'firewall-01'],
            'file_name': file.filename
        })
        
    except Exception as e:
        logging.error(f"Upload error: {str(e)}", exc_info=True)
        return safe_json_response({
            'error': str(e).encode('utf-8', 'replace').decode('utf-8'),
            'type': 'upload_error'
        }, 500)

@api_bp.route('/process', methods=['POST'])
def process_file():
    """Process file with mappings"""
    try:
        data = request.json
        return safe_json_response({
            'success': True,
            'message': 'File processed successfully',
            'result': {'processed_records': 1000}
        })
    except Exception as e:
        logging.error(f"Processing error: {str(e)}", exc_info=True)
        return safe_json_response({
            'error': str(e).encode('utf-8', 'replace').decode('utf-8'),
            'type': 'processing_error'
        }, 500)

# Register the API blueprint
app.register_blueprint(api_bp)

if __name__ == "__main__":
    print("\n🚀 Starting Yosai Intel Dashboard API...")
    print("   Available at: http://localhost:5001")
    print("   Health check: http://localhost:5001/api/v1/health")
    print("   Upload endpoint: http://localhost:5001/api/v1/upload")
    
    app.run(host='0.0.0.0', port=5001, debug=True)
