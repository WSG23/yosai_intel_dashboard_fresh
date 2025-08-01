"""Endpoints for saving and applying file mappings."""

from flask import Blueprint
from flask_apispec import doc
from pydantic import BaseModel

from yosai_intel_dashboard.src.core.unicode import clean_unicode_surrogates
from yosai_intel_dashboard.src.error_handling import ErrorCategory, ErrorHandler, api_error_response
from yosai_intel_dashboard.src.utils.pydantic_decorators import validate_input, validate_output


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


def create_mappings_blueprint(
    upload_service,
    device_service,
    column_service,
    *,
    handler: ErrorHandler | None = None,
) -> Blueprint:
    """Return a blueprint for managing mappings."""

    mappings_bp = Blueprint("mappings", __name__)
    err_handler = handler or ErrorHandler()

    @mappings_bp.route("/v1/mappings/columns", methods=["POST"])
    @doc(
        description="Save column mappings",
        tags=["mappings"],
        responses={200: "Success", 400: "Invalid input", 500: "Server Error"},
    )
    @validate_input(FileMappingSchema)
    @validate_output(SuccessSchema)
    def save_column_mappings_route(payload: FileMappingSchema):
        """Persist column mappings for a processed file."""
        try:
            file_id = payload.file_id
            mappings = payload.mappings or {}

            if not file_id:
                return api_error_response(
                    ValueError("file_id is required"),
                    ErrorCategory.INVALID_INPUT,
                    handler=err_handler,
                )

            column_service.save_column_mappings(file_id, mappings)

            return {"status": "success"}, 200
        except KeyError as exc:  # pragma: no cover - defensive
            return api_error_response(exc, ErrorCategory.INTERNAL, handler=err_handler)
        except Exception as exc:  # pragma: no cover - defensive
            return api_error_response(exc, ErrorCategory.INTERNAL, handler=err_handler)

    @mappings_bp.route("/v1/mappings/devices", methods=["POST"])
    @doc(
        description="Save device mappings",
        tags=["mappings"],
        responses={200: "Success", 400: "Invalid input", 500: "Server Error"},
    )
    @validate_input(FileMappingSchema)
    @validate_output(SuccessSchema)
    def save_device_mappings_route(payload: FileMappingSchema):
        """Persist device mappings for a processed file."""
        try:
            file_id = payload.file_id
            mappings = payload.mappings or {}

            if not file_id:
                return api_error_response(
                    ValueError("file_id is required"),
                    ErrorCategory.INVALID_INPUT,
                    handler=err_handler,
                )

            device_service.save_device_mappings(file_id, mappings)

            return {"status": "success"}, 200
        except KeyError as exc:  # pragma: no cover - defensive
            return api_error_response(exc, ErrorCategory.INTERNAL, handler=err_handler)
        except Exception as exc:  # pragma: no cover - defensive
            return api_error_response(exc, ErrorCategory.INTERNAL, handler=err_handler)

    @mappings_bp.route("/v1/mappings/save", methods=["POST"])
    @doc(
        description="Save mappings",
        tags=["mappings"],
        responses={200: "Success", 500: "Server Error"},
    )
    @validate_input(MappingSaveSchema)
    @validate_output(SuccessSchema)
    def save_mappings(payload: MappingSaveSchema):
        """Save column or device mappings."""
        try:
            filename = payload.filename
            mapping_type = payload.mapping_type

            if mapping_type == "column":
                column_mappings = payload.column_mappings or {}
                column_service.save_column_mappings(filename, column_mappings)
            elif mapping_type == "device":
                device_mappings = payload.device_mappings or {}
                for device_name, mapping in device_mappings.items():
                    device_service.save_user_device_mapping(
                        filename=filename,
                        device_name=device_name,
                        device_type=mapping.get("device_type", "unknown"),
                        location=mapping.get("location"),
                        properties=mapping.get("properties", {}),
                    )

            return {"status": "success"}, 200
        except Exception as e:  # pragma: no cover - defensive
            return api_error_response(e, ErrorCategory.INTERNAL, handler=err_handler)

    @mappings_bp.route("/v1/process-enhanced", methods=["POST"])
    @doc(
        description="Process data with mappings",
        tags=["mappings"],
        responses={200: "Success", 404: "Not Found", 500: "Server Error"},
    )
    @validate_input(ProcessSchema)
    @validate_output(SuccessSchema)
    def process_enhanced_data(payload: ProcessSchema):
        """Process data with applied mappings."""
        try:
            filename = payload.filename
            column_mappings = payload.column_mappings or {}
            device_mappings = payload.device_mappings or {}

            stored_data = upload_service.store.get_all_data()
            df = stored_data.get(filename)

            if df is None:
                return api_error_response(
                    FileNotFoundError("File data not found"),
                    ErrorCategory.NOT_FOUND,
                    handler=err_handler,
                )

            if column_mappings:
                df = df.rename(columns=column_mappings)

            if device_mappings and "device_name" in df.columns:
                df["device_type"] = df["device_name"].map(
                    lambda x: device_mappings.get(x, {}).get("device_type", "unknown")
                )
                df["location"] = df["device_name"].map(
                    lambda x: device_mappings.get(x, {}).get("location", "")
                )

            enhanced_filename = f"enhanced_{filename}"
            upload_service.store.store_data(enhanced_filename, df)

            return {
                "status": "success",
                "enhanced_filename": enhanced_filename,
                "rows": len(df),
                "columns": len(df.columns),
            }, 200
        except Exception as e:  # pragma: no cover - defensive
            return api_error_response(e, ErrorCategory.INTERNAL, handler=err_handler)

    return mappings_bp
