from flask import Blueprint, request, jsonify

from utils.api_error import error_response

# Shared container ensures services are available across blueprints
from core.container import container
from config.service_registration import register_upload_services

if not container.has("upload_processor"):
    register_upload_services(container)

mappings_bp = Blueprint('mappings', __name__)

@mappings_bp.route('/v1/mappings/columns', methods=['POST'])
def save_column_mappings_route():
    """Persist column mappings for a processed file."""
    try:
        payload = request.get_json(force=True)
        file_id = payload.get('file_id')
        mappings = payload.get('mappings', {})

        if not file_id:
            return error_response('missing_file_id', 'file_id is required'), 400

        service = container.get('consolidated_learning_service')
        service.save_column_mappings(file_id, mappings)

        return jsonify({'status': 'success'}), 200
    except KeyError as exc:
        return error_response('bad_request', str(exc)), 400
    except Exception as exc:
        return error_response('server_error', str(exc)), 500

@mappings_bp.route('/v1/mappings/devices', methods=['POST'])
def save_device_mappings_route():
    """Persist device mappings for a processed file."""
    try:
        payload = request.get_json(force=True)
        file_id = payload.get('file_id')
        mappings = payload.get('mappings', {})

        if not file_id:
            return error_response('missing_file_id', 'file_id is required'), 400

        service = container.get('device_learning_service')
        service.save_device_mappings(file_id, mappings)

        return jsonify({'status': 'success'}), 200
    except KeyError as exc:
        return error_response('bad_request', str(exc)), 400
    except Exception as exc:
        return error_response('server_error', str(exc)), 500

@mappings_bp.route('/v1/mappings/save', methods=['POST'])
def save_mappings():
    """Save column or device mappings"""
    try:
        data = request.json
        filename = data.get('filename')
        mapping_type = data.get('mapping_type')
        
        # Get services

        if mapping_type == 'column':
            # Save column mappings
            column_mappings = data.get('column_mappings', {})
            
            # Use consolidated learning service if available
            learning_service = container.get("consolidated_learning_service")
            if learning_service:
                learning_service.save_column_mappings(filename, column_mappings)
            
        elif mapping_type == 'device':
            # Save device mappings
            device_mappings = data.get('device_mappings', {})
            
            device_service = container.get("device_learning_service")
            if device_service:
                # Save each device mapping
                for device_name, mapping in device_mappings.items():
                    device_service.save_user_device_mapping(
                        filename=filename,
                        device_name=device_name,
                        device_type=mapping.get('device_type', 'unknown'),
                        location=mapping.get('location'),
                        properties=mapping.get('properties', {})
                    )
        
        return jsonify({'status': 'success'}), 200

    except Exception as e:
        return error_response('server_error', str(e)), 500

@mappings_bp.route('/v1/process-enhanced', methods=['POST'])
def process_enhanced_data():
    """Process data with applied mappings"""
    try:
        data = request.json
        filename = data.get('filename')
        column_mappings = data.get('column_mappings', {})
        device_mappings = data.get('device_mappings', {})
        
        # Get services
        upload_service = container.get("upload_processor")
        
        # Get the dataframe
        stored_data = upload_service.store.get_all_data()
        df = stored_data.get(filename)
        
        if df is None:
            return error_response('not_found', 'File data not found'), 404
        
        # Apply column mappings (rename columns)
        if column_mappings:
            df = df.rename(columns=column_mappings)
        
        # Apply device mappings (add device metadata)
        if device_mappings:
            # Add device type column if device_name exists
            if 'device_name' in df.columns:
                df['device_type'] = df['device_name'].map(
                    lambda x: device_mappings.get(x, {}).get('device_type', 'unknown')
                )
                df['location'] = df['device_name'].map(
                    lambda x: device_mappings.get(x, {}).get('location', '')
                )
        
        # Store enhanced data
        enhanced_filename = f"enhanced_{filename}"
        upload_service.store.store_data(enhanced_filename, df)
        
        return jsonify({
            'status': 'success',
            'enhanced_filename': enhanced_filename,
            'rows': len(df),
            'columns': len(df.columns)
        }), 200
        
    except Exception as e:
        return error_response('server_error', str(e)), 500
