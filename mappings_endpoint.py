from flask import Blueprint, abort, request
from flask_apispec import doc
from pydantic import BaseModel

from utils.pydantic_decorators import validate_input, validate_output

from config.service_registration import register_upload_services

# Shared container ensures services are available across blueprints
from core.container import container
from core.unicode import clean_unicode_surrogates

if not container.has("upload_processor"):
    register_upload_services(container)

mappings_bp = Blueprint("mappings", __name__)


class FileMappingSchema(BaseModel):
    file_id: str
    mappings: dict | None = None


class MappingSaveSchema(BaseModel):
    filename: str
    mapping_type: str | None = None
    column_mappings: dict | None = None
    device_mappings: dict | None = None


class ProcessSchema(BaseModel):
    filename: str
    column_mappings: dict | None = None
    device_mappings: dict | None = None


class SuccessSchema(BaseModel):
    status: str
    enhanced_filename: str | None = None
    rows: int | None = None
    columns: int | None = None


@mappings_bp.route("/v1/mappings/columns", methods=["POST"])
@doc(description="Save column mappings", tags=["mappings"])
@validate_input(FileMappingSchema)
@validate_output(SuccessSchema)
def save_column_mappings_route(payload: FileMappingSchema):
    """Persist column mappings for a processed file."""
    try:
        file_id = payload.file_id
        mappings = payload.mappings or {}

        if not file_id:
            abort(400, description="file_id is required")

        service = container.get("consolidated_learning_service")
        service.save_column_mappings(file_id, mappings)

        return {"status": "success"}, 200
    except KeyError as exc:
        abort(500, description=clean_unicode_surrogates(exc))
    except Exception as exc:
        abort(500, description=clean_unicode_surrogates(exc))


@mappings_bp.route("/v1/mappings/devices", methods=["POST"])
@doc(description="Save device mappings", tags=["mappings"])
@validate_input(FileMappingSchema)
@validate_output(SuccessSchema)
def save_device_mappings_route(payload: FileMappingSchema):
    """Persist device mappings for a processed file."""
    try:
        file_id = payload.file_id
        mappings = payload.mappings or {}

        if not file_id:
            abort(400, description="file_id is required")

        service = container.get("device_learning_service")
        service.save_device_mappings(file_id, mappings)

        return {"status": "success"}, 200
    except KeyError as exc:
        abort(500, description=clean_unicode_surrogates(exc))
    except Exception as exc:
        abort(500, description=clean_unicode_surrogates(exc))


@mappings_bp.route("/v1/mappings/save", methods=["POST"])
@doc(description="Save mappings", tags=["mappings"])
@validate_input(MappingSaveSchema)
@validate_output(SuccessSchema)
def save_mappings(payload: MappingSaveSchema):
    """Save column or device mappings"""
    try:
        filename = payload.filename
        mapping_type = payload.mapping_type

        # Get services

        if mapping_type == "column":
            # Save column mappings
            column_mappings = payload.column_mappings or {}

            # Use consolidated learning service if available
            learning_service = container.get("consolidated_learning_service")
            if learning_service:
                learning_service.save_column_mappings(filename, column_mappings)

        elif mapping_type == "device":
            # Save device mappings
            device_mappings = payload.device_mappings or {}

            device_service = container.get("device_learning_service")
            if device_service:
                # Save each device mapping
                for device_name, mapping in device_mappings.items():
                    device_service.save_user_device_mapping(
                        filename=filename,
                        device_name=device_name,
                        device_type=mapping.get("device_type", "unknown"),
                        location=mapping.get("location"),
                        properties=mapping.get("properties", {}),
                    )

        return {"status": "success"}, 200

    except Exception as e:
        abort(500, description=clean_unicode_surrogates(e))


@mappings_bp.route("/v1/process-enhanced", methods=["POST"])
@doc(description="Process data with mappings", tags=["mappings"])
@validate_input(ProcessSchema)
@validate_output(SuccessSchema)
def process_enhanced_data(payload: ProcessSchema):
    """Process data with applied mappings"""
    try:
        filename = payload.filename
        column_mappings = payload.column_mappings or {}
        device_mappings = payload.device_mappings or {}

        # Get services
        upload_service = container.get("upload_processor")

        # Get the dataframe
        stored_data = upload_service.store.get_all_data()
        df = stored_data.get(filename)

        if df is None:
            abort(404, description="File data not found")

        # Apply column mappings (rename columns)
        if column_mappings:
            df = df.rename(columns=column_mappings)

        # Apply device mappings (add device metadata)
        if device_mappings:
            # Add device type column if device_name exists
            if "device_name" in df.columns:
                df["device_type"] = df["device_name"].map(
                    lambda x: device_mappings.get(x, {}).get("device_type", "unknown")
                )
                df["location"] = df["device_name"].map(
                    lambda x: device_mappings.get(x, {}).get("location", "")
                )

        # Store enhanced data
        enhanced_filename = f"enhanced_{filename}"
        upload_service.store.store_data(enhanced_filename, df)

        return {
            "status": "success",
            "enhanced_filename": enhanced_filename,
            "rows": len(df),
            "columns": len(df.columns),
        }, 200

    except Exception as e:
        abort(500, description=clean_unicode_surrogates(e))
