from flask import Blueprint, request, jsonify

from utils.api_error import error_response
from core.unicode_handler import clean_unicode_surrogates

# Shared container ensures services are available across blueprints
from core.container import container
import os
os.environ.setdefault("LIGHTWEIGHT_SERVICES", "1")
from services.mappings import save_column_mappings, save_device_mappings

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

        save_column_mappings(file_id, mappings)

        return jsonify({'status': 'success'}), 200
    except KeyError as exc:
        return error_response('server_error', clean_unicode_surrogates(exc)), 500
    except Exception as exc:
        return error_response('server_error', clean_unicode_surrogates(exc)), 500

@mappings_bp.route('/v1/mappings/devices', methods=['POST'])
def save_device_mappings_route():
    """Persist device mappings for a processed file."""
    try:
        payload = request.get_json(force=True)
        file_id = payload.get('file_id')
        mappings = payload.get('mappings', {})

        if not file_id:
            return error_response('missing_file_id', 'file_id is required'), 400

        save_device_mappings(file_id, mappings)

        return jsonify({'status': 'success'}), 200
    except KeyError as exc:
        return error_response('server_error', clean_unicode_surrogates(exc)), 500
    except Exception as exc:
        return error_response('server_error', clean_unicode_surrogates(exc)), 500

@mappings_bp.route('/v1/mappings/save', methods=['POST'])
def save_mappings():
    """Save column or device mappings"""
    try:
        data = request.json
        filename = data.get('filename')
        mapping_type = data.get('mapping_type')
        
        if mapping_type == 'column':
            column_mappings = data.get('column_mappings', {})
            save_column_mappings(filename, column_mappings)

        elif mapping_type == 'device':
            device_mappings = data.get('device_mappings', {})
            save_device_mappings(filename, device_mappings)
        
        return jsonify({'status': 'success'}), 200

    except Exception as e:
        return error_response('server_error', clean_unicode_surrogates(e)), 500

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
        return error_response('server_error', clean_unicode_surrogates(e)), 500
