"""API endpoints for device mapping suggestions."""

import pandas as pd
from flask import Blueprint, jsonify, request
from flask_apispec import doc
from pydantic import BaseModel

from services.upload.service_registration import register_upload_services

# Use the shared DI container for dependency resolution
from core.container import container
from error_handling import ErrorCategory, ErrorHandler, api_error_response
from utils.pydantic_decorators import validate_input, validate_output

if not container.has("upload_processor"):
    register_upload_services(container)

device_bp = Blueprint("device", __name__)

handler = ErrorHandler()


class DeviceSuggestSchema(BaseModel):
    filename: str
    column_mappings: dict[str, str] | None = None


class DeviceResponseSchema(BaseModel):
    devices: list[str]
    device_mappings: dict


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

    from services.ai_mapping_store import ai_mapping_store

    ai_mapping_store.clear()
    learned_applied = upload_service.auto_apply_learned_mappings(df, filename)

    if not learned_applied:
        from yosai_intel_dashboard.src.components import simple_device_mapping as sdm

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
@doc(
    description="Suggest device mappings",
    tags=["device"],
    responses={200: "Success", 404: "File not found", 500: "Server Error"},
)
@validate_input(DeviceSuggestSchema)
@validate_output(DeviceResponseSchema)
def suggest_devices(payload: DeviceSuggestSchema):
    """Get device suggestions using DeviceLearningService"""
    try:
        filename = payload.filename
        column_mappings = payload.column_mappings or {}

        device_service = container.get("device_learning_service")
        upload_service = container.get("upload_processor")

        df = load_stored_data(filename, upload_service)
        if df is None:
            return api_error_response(
                FileNotFoundError("File data not found"),
                ErrorCategory.NOT_FOUND,
                handler=handler,
            )

        device_column = determine_device_column(column_mappings, df)
        devices = df[device_column].dropna().unique().tolist() if device_column else []

        device_mappings = build_device_mappings(
            filename, df, device_service, upload_service
        )

        return {"devices": devices, "device_mappings": device_mappings}, 200

    except Exception as e:
        return api_error_response(e, ErrorCategory.INTERNAL, handler=handler)
