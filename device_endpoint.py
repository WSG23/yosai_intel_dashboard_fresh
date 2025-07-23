from flask import Blueprint, request, jsonify

from utils.api_error import error_response
import pandas as pd

# Use the shared DI container for dependency resolution
from core.container import container
from config.service_registration import register_upload_services

if not container.has("upload_processor"):
    register_upload_services(container)

device_bp = Blueprint('device', __name__)


def load_stored_data(filename: str, upload_service) -> pd.DataFrame | None:
    """Return the stored dataframe for *filename* from ``upload_service``."""
    stored_data = upload_service.store.get_all_data()
    return stored_data.get(filename)


def determine_device_column(column_mappings: dict, df: pd.DataFrame) -> str | None:
    """Find the source column mapped as the device name."""
    for source_col, mapped_col in column_mappings.items():
        if mapped_col in ["device_name", "device", "hostname"] and source_col in df.columns:
            return source_col
    return None


def build_device_mappings(
    filename: str,
    df: pd.DataFrame,
    device_service,
    upload_service,
) -> dict:
    """Construct the device mapping dictionary for *df* and *filename*."""
    device_mappings: dict[str, dict] = {}

    user_mappings = device_service.get_user_device_mappings(filename)
    if user_mappings:
        for device, mapping in user_mappings.items():
            device_mappings[device] = {
                "device_type": mapping.get("device_type", "unknown"),
                "location": mapping.get("location"),
                "properties": mapping.get("properties", {}),
                "confidence": 1.0,
                "source": "user_confirmed",
            }
    else:
        from services.ai_mapping_store import ai_mapping_store

        ai_mapping_store.clear()
        learned_applied = upload_service.auto_apply_learned_mappings(df, filename)

        if not learned_applied:
            from components import simple_device_mapping as sdm

            sdm.generate_ai_device_defaults(df, "auto")

        store_mappings = ai_mapping_store.all()
        for device, mapping in store_mappings.items():
            device_mappings[device] = {
                "device_type": mapping.get("device_type", "unknown"),
                "location": mapping.get("location"),
                "properties": mapping.get("properties", {}),
                "confidence": mapping.get("confidence", 0.8),
                "source": mapping.get("source", "ai_suggested"),
            }

    return device_mappings

@device_bp.route('/v1/ai/suggest-devices', methods=['POST'])
def suggest_devices():
    """Get device suggestions using DeviceLearningService"""
    try:
        data = request.json
        filename = data.get('filename')
        column_mappings = data.get('column_mappings', {})
        
        device_service = container.get("device_learning_service")
        upload_service = container.get("upload_processor")

        df = load_stored_data(filename, upload_service)
        if df is None:
            return error_response('not_found', 'File data not found'), 404

        device_column = determine_device_column(column_mappings, df)
        devices = (
            df[device_column].dropna().unique().tolist() if device_column else []
        )

        device_mappings = build_device_mappings(
            filename, df, device_service, upload_service
        )

        return jsonify({
            'devices': devices,
            'device_mappings': device_mappings
        }), 200
        
    except Exception as e:
        return error_response('server_error', str(e)), 500
