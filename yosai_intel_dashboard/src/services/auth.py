from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from yosai_intel_dashboard.src.services.security.jwt_service import (
    TokenValidationError,
    verify_service_jwt,
)


def verify_jwt_token(
    token: str,
    validator=verify_service_jwt,
    *,
    audience: str | None = None,
    subject: str | None = None,
) -> dict:
    """Return JWT claims or raise HTTPException with precise error codes."""
    kwargs = {k: v for k, v in {"audience": audience, "subject": subject}.items() if v is not None}
    try:
        claims = validator(token, **kwargs)
    except TokenValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": exc.code, "message": exc.code},
        ) from exc
    if claims is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "unauthorized", "message": "unauthorized"},
        )
    return claims


_bearer_scheme = HTTPBearer()


def require_service_token(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    validator=verify_service_jwt,
) -> dict:
    """FastAPI dependency validating service JWT tokens."""
    return verify_jwt_token(credentials.credentials, validator)


def validate_authorization_header(
    authorization: str, validator=verify_service_jwt
) -> dict:
    """Validate a Bearer ``authorization`` header and return JWT claims."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "unauthorized", "message": "unauthorized"},
        )
    token = authorization.split(" ", 1)[1]
    return verify_jwt_token(token, validator)


__all__ = [
    "verify_jwt_token",
    "require_service_token",
    "validate_authorization_header",
]
