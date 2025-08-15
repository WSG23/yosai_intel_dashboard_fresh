"""Token refresh API endpoint using FastAPI."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from shared.errors.types import CODE_TO_STATUS, ErrorCode

from yosai_intel_dashboard.src.services.security import refresh_access_token


class RefreshRequest(BaseModel):
    refresh_token: str
    """Request payload schema for token refresh."""


class AccessTokenResponse(BaseModel):
    """Response schema containing a new access token."""

    access_token: str


def create_token_router(*, handler: object | None = None) -> APIRouter:
    """Return an APIRouter for refreshing access tokens."""

    router = APIRouter()

    @router.post(
        "/v1/token/refresh",
        response_model=AccessTokenResponse,
        responses={401: {"description": "Unauthorized"}},
    )
    async def refresh_token_endpoint(payload: RefreshRequest):  # noqa: D401
        """Refresh the access token using the provided refresh token."""
        new_token = refresh_access_token(payload.refresh_token)
        if not new_token:
            status = CODE_TO_STATUS.get(ErrorCode.UNAUTHORIZED, 401)
            return JSONResponse(
                status_code=status,
                content={
                    "code": ErrorCode.UNAUTHORIZED.value,
                    "message": "invalid refresh token",
                    "details": None,
                },
            )
        return {"access_token": new_token}

    return router
