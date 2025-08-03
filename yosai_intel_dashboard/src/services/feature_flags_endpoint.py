from __future__ import annotations

"""Feature flag management endpoints with role-based access control."""

from flask import Blueprint
from flask_apispec import doc
from pydantic import BaseModel

from yosai_intel_dashboard.src.error_handling import (
    ErrorCategory,
    ErrorHandler,
    api_error_response,
)
from yosai_intel_dashboard.src.services.feature_flags import (
    feature_flags,
    get_evaluation_context,
)
from yosai_intel_dashboard.src.services.security import require_role
from yosai_intel_dashboard.src.utils.pydantic_decorators import validate_input


class FlagUpdateSchema(BaseModel):
    """Payload schema for creating or updating a flag."""

    value: bool


def create_feature_flags_blueprint(*, handler: ErrorHandler | None = None) -> Blueprint:
    """Return a blueprint exposing flag CRUD operations."""

    flags_bp = Blueprint("feature_flags", __name__)
    err_handler = handler or ErrorHandler()

    @flags_bp.route("/v1/flags", methods=["GET"])
    @doc(
        description="List all feature flags (requires `feature_admin`).",
        tags=["feature_flags"],
        responses={200: "Success", 403: "Forbidden"},
    )
    @require_role("feature_admin")
    def list_flags():
        """Return all feature flags."""
        return feature_flags.get_all(), 200

    @flags_bp.route("/v1/flags/<name>", methods=["GET"])
    @doc(
        description="Get a feature flag value (requires `feature_admin`).",
        tags=["feature_flags"],
        responses={200: "Success", 404: "Not Found", 403: "Forbidden"},
    )
    @require_role("feature_admin")
    def get_flag(name: str):
        ctx = get_evaluation_context()
        value = feature_flags.is_enabled(name, context=ctx)
        if name not in feature_flags.get_all():
            return api_error_response(
                KeyError("flag not found"),
                ErrorCategory.NOT_FOUND,
                handler=err_handler,
            )
        return {"name": name, "value": value}, 200

    @flags_bp.route("/v1/flags/<name>", methods=["PUT"])
    @doc(
        description="Create or update a feature flag (requires `feature_admin`).",
        tags=["feature_flags"],
        responses={200: "Success", 403: "Forbidden"},
    )
    @validate_input(FlagUpdateSchema)
    @require_role("feature_admin")
    def set_flag(name: str, payload: FlagUpdateSchema):
        feature_flags.set_flag(name, payload.value)
        return {"name": name, "value": payload.value}, 200

    @flags_bp.route("/v1/flags/<name>", methods=["DELETE"])
    @doc(
        description="Delete a feature flag (requires `feature_admin`).",
        tags=["feature_flags"],
        responses={200: "Deleted", 404: "Not Found", 403: "Forbidden"},
    )
    @require_role("feature_admin")
    def delete_flag(name: str):
        if not feature_flags.delete_flag(name):
            return api_error_response(
                KeyError("flag not found"),
                ErrorCategory.NOT_FOUND,
                handler=err_handler,
            )
        return {"status": "deleted", "name": name}, 200

    return flags_bp


__all__ = ["create_feature_flags_blueprint"]
