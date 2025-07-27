from flask import Blueprint, abort
from pydantic import BaseModel
from utils.pydantic_decorators import validate_input, validate_output
from services.security import refresh_access_token


token_bp = Blueprint("token", __name__)


class RefreshRequest(BaseModel):
    refresh_token: str


class AccessTokenResponse(BaseModel):
    access_token: str


@token_bp.route("/v1/token/refresh", methods=["POST"])
@validate_input(RefreshRequest)
@validate_output(AccessTokenResponse)
def refresh_token_endpoint(payload: RefreshRequest):
    new_token = refresh_access_token(payload.refresh_token)
    if not new_token:
        abort(401, description="invalid refresh token")
    return {"access_token": new_token}
