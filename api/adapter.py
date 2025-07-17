import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, jsonify, request, Blueprint
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from flask_cors import CORS
from api.analytics_endpoints import register_analytics_blueprints
import logging
import json
from services.data_enhancer import get_ai_column_suggestions
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


@api_bp.route('/ai/suggest-columns', methods=['POST'])
def suggest_column_mappings():
    """Get AI suggestions for column mappings"""
    try:
        data = request.json
        columns = data.get('columns', [])
        
        # Import and use the actual AI function
        from services.data_enhancer import get_ai_column_suggestions
        ai_suggestions = get_ai_column_suggestions(columns)
        
        # Convert format for frontend
        suggestions = {}
        for col, suggestion in ai_suggestions.items():
            if suggestion['field']:  # Only include if there's a suggestion
                suggestions[col] = suggestion['field']
        
        logging.info(f"AI suggestions: {suggestions}")
        
        return safe_json_response({
            'suggestions': suggestions,
            'user_id': data.get('user_id', 'default')
        })
        
    except Exception as e:
        logging.error(f"AI column suggestion error: {str(e)}", exc_info=True)
        return safe_json_response({'error': str(e)}, 500)
@api_bp.route('/ai/suggest-devices', methods=['POST'])
def suggest_device_mappings():
    """Get AI suggestions for device mappings"""
    try:
        data = request.json
        devices = data.get('devices', [])
        column_mappings = data.get('column_mappings', {})
        user_id = data.get('user_id', 'default')
        
        # Import your existing AI device mapping function
        # from services.device_learning_service import DeviceLearningService
        
        # Mock AI suggestions - replace with actual function
        suggestions = {}
        
        for device in devices:
            device_lower = device.lower()
            if 'exit' in device_lower:
                suggestions[device] = {
                    'type': 'exit',
                    'location': 'building_exit',
                    'security_level': 'high'
                }
            elif 'entrance' in device_lower or 'entry' in device_lower:
                suggestions[device] = {
                    'type': 'entrance',
                    'location': 'main_entrance',
                    'security_level': 'high'
                }
            elif 'stair' in device_lower:
                suggestions[device] = {
                    'type': 'stairwell',
                    'location': 'emergency_exit',
                    'security_level': 'medium'
                }
            else:
                suggestions[device] = {
                    'type': 'unknown',
                    'location': 'general',
                    'security_level': 'standard'
                }
        
        # In production:
        # device_service = DeviceLearningService()
        # suggestions = device_service.get_device_suggestions(devices, column_mappings, user_id)
        
        return safe_json_response({
            'suggestions': suggestions,
            'user_id': user_id
        })
        
    except Exception as e:
        logging.error(f"AI device suggestion error: {str(e)}", exc_info=True)
        return safe_json_response({'error': str(e)}, 500)

@api_bp.route('/mappings/save', methods=['POST'])
def save_mappings():
    """Save user mappings for future learning"""
    try:
        data = request.json
        user_id = data.get('user_id', 'default')
        file_pattern = data.get('file_pattern', '')
        column_mappings = data.get('column_mappings', {})
        device_mappings = data.get('device_mappings', {})
        
        # Import your existing save function
        # from services.mapping_persistence_service import save_user_mappings
        
        # In production:
        # save_user_mappings(user_id, file_pattern, column_mappings, device_mappings)
        
        logging.info(f"Saved mappings for user {user_id}: columns={column_mappings}, devices={device_mappings}")
        
        return safe_json_response({
            'success': True,
            'message': 'Mappings saved for future use'
        })
        
    except Exception as e:
        logging.error(f"Save mappings error: {str(e)}", exc_info=True)
        return safe_json_response({'error': str(e)}, 500)
# Add these to api/adapter.py after the existing endpoints

@api_bp.route('/ai/suggest-columns', methods=['POST'])
def suggest_column_mappings():
    """Get AI suggestions for column mappings"""
    try:
        data = request.json
        columns = data.get('columns', [])
        
        # Use existing function from base code
        from services.data_enhancer import get_ai_column_suggestions
        ai_suggestions = get_ai_column_suggestions(columns)
        
        # Format: {'column': {'field': 'mapped_field', 'confidence': 0.8}}
        return safe_json_response({
            'suggestions': ai_suggestions,
            'success': True
        })
        
    except Exception as e:
        logging.error(f"AI column suggestion error: {str(e)}", exc_info=True)
        return safe_json_response({'error': str(e)}, 500)

@api_bp.route('/ai/suggest-devices', methods=['POST'])
def suggest_device_mappings():
    """Get AI suggestions for device mappings using DeviceLearningService"""
    try:
        data = request.json
        devices = data.get('devices', [])
        filename = data.get('filename', '')
        
        # Use existing DeviceLearningService
        from services.device_learning_service import DeviceLearningService
        from services.ai_device_generator import ai_mapping_store
        
        device_service = DeviceLearningService()
        
        # Get AI suggestions for each device
        suggestions = {}
        for device in devices:
            # Check AI mapping store first
            ai_data = ai_mapping_store.get(device)
            if ai_data:
                suggestions[device] = ai_data
            else:
                # Default structure based on your base code
                suggestions[device] = {
                    'floor_number': '',
                    'security_level': 5,
                    'is_entry': 'entry' in device.lower(),
                    'is_exit': 'exit' in device.lower(),
                    'is_elevator': 'elevator' in device.lower(),
                    'is_stairwell': 'stair' in device.lower()
                }
        
        return safe_json_response({
            'suggestions': suggestions,
            'success': True
        })
        
    except Exception as e:
        logging.error(f"AI device suggestion error: {str(e)}", exc_info=True)
        return safe_json_response({'error': str(e)}, 500)

@api_bp.route('/mappings/save', methods=['POST'])
def save_mappings():
    """Save mappings for learning using existing services"""
    try:
        data = request.json
        
        # Use consolidated learning service
        from services.consolidated_learning_service import get_learning_service
        
        learning_service = get_learning_service()
        
        # Save column mappings
        if data.get('column_mappings'):
            learning_service.remember_column_mappings(
                data['filename'],
                data['column_mappings']
            )
        
        # Save device mappings
        if data.get('device_mappings'):
            learning_service.remember_device_mappings(
                data['filename'],
                data['device_mappings']
            )
        
        return safe_json_response({
            'success': True,
            'message': 'Mappings saved for future learning'
        })
        
    except Exception as e:
        logging.error(f"Save mappings error: {str(e)}", exc_info=True)
        return safe_json_response({'error': str(e)}, 500)
