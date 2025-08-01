from fastapi import HTTPException, status

from yosai_intel_dashboard.src.services.security.jwt_service import verify_service_jwt


def verify_jwt_token(token: str) -> dict:
    """Return JWT claims or raise HTTPException if invalid."""
    claims = verify_service_jwt(token)
    if claims is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "unauthorized", "message": "unauthorized"},
        )
    return claims
