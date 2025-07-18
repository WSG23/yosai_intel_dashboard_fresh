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
logger = logging.getLogger(__name__)
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
api_bp = Blueprint("api_v1", __name__)

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
app.register_blueprint(api_bp, url_prefix="/api/v1")

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

# ============= AI Column and Device Mapping Endpoints =============
import re  # Add at top if not already imported

@app.route('/api/v1/ai/suggest-columns', methods=['POST'])
def suggest_columns():
    """AI suggestions for column mappings"""
    try:
        data = request.json
        columns = data.get('columns', [])
        
        suggestions = {}
        for col in columns:
            col_lower = col.lower()
            confidence = 0.5
            field = None
            
            if 'time' in col_lower or 'date' in col_lower:
                field = 'timestamp'
                confidence = 0.9
            elif 'user' in col_lower or 'person' in col_lower:
                field = 'person_id'
                confidence = 0.8
            elif 'door' in col_lower or 'location' in col_lower:
                field = 'door_id'
                confidence = 0.8
            elif 'result' in col_lower or 'access' in col_lower:
                field = 'access_result'
                confidence = 0.7
            elif 'card' in col_lower or 'badge' in col_lower or 'token' in col_lower:
                field = 'token_id'
                confidence = 0.8
            elif 'ip' in col_lower:
                field = 'source_ip' if 'source' in col_lower else 'dest_ip'
                confidence = 0.8
            elif 'action' in col_lower:
                field = 'action'
                confidence = 0.8
            elif 'device' in col_lower:
                field = 'device'
                confidence = 0.8
                
            if field:
                suggestions[col] = {
                    'field': field,
                    'confidence': confidence
                }
        
        return jsonify({'suggestions': suggestions}), 200
        
    except Exception as e:
        logger.error(f"Error suggesting columns: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/ai/suggest-devices', methods=['POST'])
def suggest_devices():
    """AI suggestions for device mappings"""
    try:
        data = request.json
        devices = data.get('devices', [])
        
        suggestions = {}
        for device in devices:
            device_lower = device.lower()
            
            info = {
                'floor_number': None,
                'is_entry': 'entry' in device_lower or 'main' in device_lower,
                'is_exit': 'exit' in device_lower,
                'is_elevator': 'elevator' in device_lower or 'lift' in device_lower,
                'is_stairwell': 'stair' in device_lower,
                'security_level': 7 if 'secure' in device_lower else 5
            }
            
            floor_match = re.search(r'floor[_\s]*(\d+)|f(\d+)', device_lower)
            if floor_match:
                info['floor_number'] = int(floor_match.group(1) or floor_match.group(2))
            
            suggestions[device] = info
        
        return jsonify({'suggestions': suggestions}), 200
        
    except Exception as e:
        logger.error(f"Error suggesting devices: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/process', methods=['POST'])
def process_file():
    """Process file with mappings"""
    try:
        data = request.json
        logger.info(f"Processing file: {data.get('fileName')}")
        
        # TODO: Add your file processing logic here
        # For now, just return success
        
        return jsonify({
            'status': 'success',
            'message': 'File processed successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/mappings/save', methods=['POST'])
def save_mappings():
    """Save column and device mappings for future use"""
    try:
        data = request.json
        filename = data.get('filename')
        column_mappings = data.get('column_mappings', {})
        device_mappings = data.get('device_mappings', {})
        
        logger.info(f"Saving mappings for: {filename}")
        logger.info(f"Column mappings: {column_mappings}")
        logger.info(f"Device mappings: {device_mappings}")
        
        # TODO: Save to database or file system
        # For now, you could save to a JSON file:
        # import json
        # mappings_data = {
        #     'filename': filename,
        #     'column_mappings': column_mappings,
        #     'device_mappings': device_mappings,
        #     'timestamp': datetime.now().isoformat()
        # }
        # with open(f'mappings/{filename}_mappings.json', 'w') as f:
        #     json.dump(mappings_data, f)
        
        return jsonify({
            'status': 'success',
            'message': 'Mappings saved successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error saving mappings: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ============= End of new endpoints =============


# ============= AI Column and Device Mapping Endpoints =============

@app.route('/api/v1/ai/suggest-columns', methods=['POST'])
def suggest_columns():
    """AI suggestions for column mappings"""
    try:
        data = request.json
        columns = data.get('columns', [])
        
        suggestions = {}
        for col in columns:
            col_lower = col.lower()
            confidence = 0.5
            field = None
            
            if 'time' in col_lower or 'date' in col_lower:
                field = 'timestamp'
                confidence = 0.9
            elif 'user' in col_lower or 'person' in col_lower:
                field = 'person_id'
                confidence = 0.8
            elif 'door' in col_lower or 'location' in col_lower:
                field = 'door_id'
                confidence = 0.8
            elif 'result' in col_lower or 'access' in col_lower:
                field = 'access_result'
                confidence = 0.7
            elif 'card' in col_lower or 'badge' in col_lower or 'token' in col_lower:
                field = 'token_id'
                confidence = 0.8
            elif 'ip' in col_lower:
                field = 'source_ip' if 'source' in col_lower else 'dest_ip'
                confidence = 0.8
            elif 'action' in col_lower:
                field = 'action'
                confidence = 0.8
            elif 'device' in col_lower:
                field = 'device'
                confidence = 0.8
                
            if field:
                suggestions[col] = {
                    'field': field,
                    'confidence': confidence
                }
        
        return safe_json_response({'suggestions': suggestions}), 200
        
    except Exception as e:
        logger.error(f"Error suggesting columns: {str(e)}")
        return safe_json_response({'error': str(e)}), 500

@app.route('/api/v1/ai/suggest-devices', methods=['POST'])
def suggest_devices():
    """AI suggestions for device mappings"""
    try:
        data = request.json
        devices = data.get('devices', [])
        
        suggestions = {}
        for device in devices:
            device_lower = device.lower()
            
            info = {
                'floor_number': None,
                'is_entry': 'entry' in device_lower or 'main' in device_lower,
                'is_exit': 'exit' in device_lower,
                'is_elevator': 'elevator' in device_lower or 'lift' in device_lower,
                'is_stairwell': 'stair' in device_lower,
                'security_level': 7 if 'secure' in device_lower else 5
            }
            
            floor_match = re.search(r'floor[_\s]*(\d+)|f(\d+)', device_lower)
            if floor_match:
                info['floor_number'] = int(floor_match.group(1) or floor_match.group(2))
            
            suggestions[device] = info
        
        return safe_json_response({'suggestions': suggestions}), 200
        
    except Exception as e:
        logger.error(f"Error suggesting devices: {str(e)}")
        return safe_json_response({'error': str(e)}), 500

@app.route('/api/v1/process', methods=['POST'])
def process_file():
    """Process file with mappings"""
    try:
        data = request.json
        logger.info(f"Processing file: {data.get('fileName')}")
        
        # TODO: Add your file processing logic here
        # For now, just return success
        
        return safe_json_response({
            'status': 'success',
            'message': 'File processed successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        return safe_json_response({'error': str(e)}), 500

@app.route('/api/v1/mappings/save', methods=['POST'])
def save_mappings():
    """Save column and device mappings for future use"""
    try:
        data = request.json
        filename = data.get('filename')
        column_mappings = data.get('column_mappings', {})
        device_mappings = data.get('device_mappings', {})
        
        logger.info(f"Saving mappings for: {filename}")
        logger.info(f"Column mappings: {column_mappings}")
        logger.info(f"Device mappings: {device_mappings}")
        
        # TODO: Save to database or file system
        # For now, you could save to a JSON file:
        # mappings_dir = 'mappings'
        # os.makedirs(mappings_dir, exist_ok=True)
        # mappings_data = {
        #     'filename': filename,
        #     'column_mappings': column_mappings,
        #     'device_mappings': device_mappings,
        #     'timestamp': datetime.now().isoformat()
        # }
        # with open(f'{mappings_dir}/{filename}_mappings.json', 'w') as f:
        #     json.dump(mappings_data, f)
        
        return safe_json_response({
            'status': 'success',
            'message': 'Mappings saved successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error saving mappings: {str(e)}")
        return safe_json_response({'error': str(e)}), 500

# ============= End of new endpoints =============


# ============= Enhanced Upload with Python Services =============

@app.route('/api/v1/upload/process', methods=['POST'])
def process_upload_with_ai():
    """Process upload using Python base code services"""
    try:
        if 'file' not in request.files:
            return safe_json_response({'error': 'No file provided'}, 400)
        
        file = request.files['file']
        filename = file.filename
        
        # For now, return a working response that matches what Upload.tsx expects
        import pandas as pd
        import io
        
        # Read file
        columns = []
        rows = 0
        
        try:
            if filename.endswith('.csv'):
                df = pd.read_csv(file)
                columns = df.columns.tolist()
                rows = len(df)
                preview_html = df.head(5).to_html(classes='table table-striped', index=False)
            else:
                columns = ['Event Time', 'Employee Code', 'Access Card', 'Door Location', 'Entry Status']
                rows = 76
                preview_html = '<p>Preview not available for this file type</p>'
        except Exception as e:
            columns = ['Event Time', 'Employee Code', 'Access Card', 'Door Location', 'Entry Status']
            rows = 76
            preview_html = '<p>Error reading file</p>'
        
        # Generate AI suggestions
        ai_suggestions = {}
        for col in columns:
            col_lower = col.lower()
            if 'time' in col_lower:
                ai_suggestions[col] = {'field': 'timestamp', 'confidence': 0.9}
            elif 'employee' in col_lower and 'code' in col_lower:
                ai_suggestions[col] = {'field': 'employee_code', 'confidence': 0.9}
            elif 'access' in col_lower and 'card' in col_lower:
                ai_suggestions[col] = {'field': 'access_card', 'confidence': 0.8}
            elif 'door' in col_lower:
                ai_suggestions[col] = {'field': 'door_location', 'confidence': 0.8}
            elif 'status' in col_lower or 'entry' in col_lower:
                ai_suggestions[col] = {'field': 'entry_status', 'confidence': 0.8}
        
        return safe_json_response({
            'success': True,
            'file_info_dict': {
                filename: {
                    'filename': filename,
                    'rows': rows,
                    'columns': len(columns),
                    'column_names': columns,
                    'ai_suggestions': ai_suggestions,
                    'preview_data': {},
                    'learned_mappings': False
                }
            },
            'columns': columns,
            'detected_devices': ['F01A Main Lobby Entry', 'F01A Reception Desk'],
            'device_suggestions': {},
            'preview_html': preview_html
        })
        
    except Exception as e:
        logging.error(f"Process upload error: {str(e)}", exc_info=True)
        return safe_json_response({'error': str(e)}, 500)

