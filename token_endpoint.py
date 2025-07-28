from flask import Blueprint, jsonify
from error_handling import ErrorCategory, ErrorHandler
from yosai_framework.errors import CODE_TO_STATUS
from shared.errors.types import ErrorCode
from pydantic import BaseModel
from utils.pydantic_decorators import validate_input, validate_output
from services.security import refresh_access_token


token_bp = Blueprint("token", __name__)

handler = ErrorHandler()


class RefreshRequest(BaseModel):
    refresh_token: str


class AccessTokenResponse(BaseModel):
    access_token: str


@token_bp.route("/v1/token/refresh", methods=["POST"])
@validate_input(RefreshRequest)
@validate_output(AccessTokenResponse)
@doc(description="Refresh access token", tags=["token"], responses={200: "Success", 401: "Unauthorized"})
def refresh_token_endpoint(payload: RefreshRequest):
    new_token = refresh_access_token(payload.refresh_token)
    if not new_token:
        err = handler.handle(
            PermissionError("invalid refresh token"), ErrorCategory.UNAUTHORIZED
        )
        return jsonify(err.to_dict()), CODE_TO_STATUS[ErrorCode.UNAUTHORIZED]
    return {"access_token": new_token}
