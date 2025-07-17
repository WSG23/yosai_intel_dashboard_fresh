from flask import Blueprint, request, jsonify
import pandas as pd

device_bp = Blueprint('device', __name__)

@device_bp.route('/api/v1/ai/suggest-devices', methods=['POST'])
def suggest_devices():
    """Get device suggestions using DeviceLearningService"""
    try:
        data = request.json
        filename = data.get('filename')
        column_mappings = data.get('column_mappings', {})
        
        # Get services from container
        from core.service_container import ServiceContainer
        container = ServiceContainer()
        
        device_service = container.get("device_learning_service")
        upload_service = container.get("upload_processor")
        
        # Get the dataframe from store
        stored_data = upload_service.store.get_all_data()
        df = stored_data.get(filename)
        
        if df is None:
            return jsonify({'error': 'File data not found'}), 404
        
        # Get unique devices from data
        devices = []
        device_column = None
        
        # Find device column from mappings
        for source_col, mapped_col in column_mappings.items():
            if mapped_col in ['device_name', 'device', 'hostname']:
                device_column = source_col
                break
        
        if device_column and device_column in df.columns:
            devices = df[device_column].dropna().unique().tolist()
        
        # Get AI/learned mappings
        device_mappings = {}
        
        # First check for user-saved mappings
        user_mappings = device_service.get_user_device_mappings(filename)
        
        if user_mappings:
            # Use saved mappings
            for device, mapping in user_mappings.items():
                device_mappings[device] = {
                    'device_type': mapping.get('device_type', 'unknown'),
                    'location': mapping.get('location'),
                    'properties': mapping.get('properties', {}),
                    'confidence': 1.0,
                    'source': 'user_confirmed'
                }
        else:
            # Try learned mappings
            from services.ai_mapping_store import ai_mapping_store
            ai_mapping_store.clear()
            
            # Apply learned mappings
            learned_applied = upload_service.auto_apply_learned_mappings(df, filename)
            
            if not learned_applied:
                # Generate AI suggestions for new devices
                from components import simple_device_mapping as sdm
                sdm.generate_ai_device_defaults(df, "auto")
            
            # Get mappings from store
            store_mappings = ai_mapping_store.all()
            for device, mapping in store_mappings.items():
                device_mappings[device] = {
                    'device_type': mapping.get('device_type', 'unknown'),
                    'location': mapping.get('location'),
                    'properties': mapping.get('properties', {}),
                    'confidence': mapping.get('confidence', 0.8),
                    'source': mapping.get('source', 'ai_suggested')
                }
        
        return jsonify({
            'devices': devices,
            'device_mappings': device_mappings
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
