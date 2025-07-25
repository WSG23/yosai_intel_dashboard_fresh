import pandas as pd
from flask import Blueprint, abort, jsonify, request
from flask_apispec import doc, marshal_with, use_kwargs
from marshmallow import Schema, fields

# Use the shared DI container for dependency resolution
from core.container import container
from yosai_intel_dashboard.src.infrastructure.config.service_registration import (
    register_upload_services,
)

if not container.has("upload_processor"):
    register_upload_services(container)

device_bp = Blueprint("device", __name__)


class DeviceSuggestSchema(Schema):
    filename = fields.String(required=True)
    column_mappings = fields.Dict(keys=fields.String(), values=fields.String())


class DeviceResponseSchema(Schema):
    devices = fields.List(fields.String())
    device_mappings = fields.Dict()


def load_stored_data(filename: str, upload_service) -> pd.DataFrame | None:
    """Return the stored dataframe for *filename* from ``upload_service``."""
    stored_data = upload_service.store.get_all_data()
    return stored_data.get(filename)


def determine_device_column(column_mappings: dict, df: pd.DataFrame) -> str | None:
    """Find the source column mapped as the device name."""
    for source_col, mapped_col in column_mappings.items():
        if (
            mapped_col in ["device_name", "device", "hostname"]
            and source_col in df.columns
        ):
            return source_col
    return None


def build_user_device_mappings(user_mappings: dict) -> dict:
    """Convert stored user mappings into the endpoint format."""

    device_mappings: dict[str, dict] = {}
    for device, mapping in user_mappings.items():
        device_mappings[device] = {
            "device_type": mapping.get("device_type", "unknown"),
            "location": mapping.get("location"),
            "properties": mapping.get("properties", {}),
            "confidence": 1.0,
            "source": "user_confirmed",
        }
    return device_mappings


def build_ai_device_mappings(df: pd.DataFrame, filename: str, upload_service) -> dict:
    """Generate mappings for AI-suggested devices."""

    from yosai_intel_dashboard.src.services.ai_mapping_store import ai_mapping_store

    ai_mapping_store.clear()
    learned_applied = upload_service.auto_apply_learned_mappings(df, filename)

    if not learned_applied:
        from components import simple_device_mapping as sdm

        sdm.generate_ai_device_defaults(df, "auto")

    store_mappings = ai_mapping_store.all()
    device_mappings: dict[str, dict] = {}
    for device, mapping in store_mappings.items():
        device_mappings[device] = {
            "device_type": mapping.get("device_type", "unknown"),
            "location": mapping.get("location"),
            "properties": mapping.get("properties", {}),
            "confidence": mapping.get("confidence", 0.8),
            "source": mapping.get("source", "ai_suggested"),
        }
    return device_mappings


def build_device_mappings(
    filename: str,
    df: pd.DataFrame,
    device_service,
    upload_service,
) -> dict:
    """Construct the device mapping dictionary for *df* and *filename*."""
    user_mappings = device_service.get_user_device_mappings(filename)
    if user_mappings:
        return build_user_device_mappings(user_mappings)

    return build_ai_device_mappings(df, filename, upload_service)


@device_bp.route("/v1/ai/suggest-devices", methods=["POST"])
@doc(description="Suggest device mappings", tags=["device"])
@use_kwargs(DeviceSuggestSchema, location="json")
@marshal_with(DeviceResponseSchema)
def suggest_devices():
    """Get device suggestions using DeviceLearningService"""
    try:
        data = request.json
        filename = data.get("filename")
        column_mappings = data.get("column_mappings", {})

        device_service = container.get("device_learning_service")
        upload_service = container.get("upload_processor")

        df = load_stored_data(filename, upload_service)
        if df is None:
            abort(404, description="File data not found")

        device_column = determine_device_column(column_mappings, df)
        devices = df[device_column].dropna().unique().tolist() if device_column else []

        device_mappings = build_device_mappings(
            filename, df, device_service, upload_service
        )

        return jsonify({"devices": devices, "device_mappings": device_mappings}), 200

    except Exception as e:
        abort(500, description=str(e))
