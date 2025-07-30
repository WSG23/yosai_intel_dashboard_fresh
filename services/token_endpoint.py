from flask import Blueprint, jsonify
from flask_apispec import doc
from pydantic import BaseModel

from error_handling import ErrorCategory, ErrorHandler, api_error_response
from services.security import refresh_access_token
from utils.pydantic_decorators import validate_input, validate_output

token_bp = Blueprint("token", __name__)

handler = ErrorHandler()


class RefreshRequest(BaseModel):
    refresh_token: str


class AccessTokenResponse(BaseModel):
    access_token: str


@token_bp.route("/v1/token/refresh", methods=["POST"])
@validate_input(RefreshRequest)
@validate_output(AccessTokenResponse)
@doc(
    description="Refresh access token",
    tags=["token"],
    responses={200: "Success", 401: "Unauthorized"},
)
def refresh_token_endpoint(payload: RefreshRequest):
    new_token = refresh_access_token(payload.refresh_token)
    if not new_token:
        return api_error_response(
            PermissionError("invalid refresh token"),
            ErrorCategory.UNAUTHORIZED,
            handler=handler,
        )
    return {"access_token": new_token}
