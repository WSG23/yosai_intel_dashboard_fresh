from __future__ import annotations

from fastapi import APIRouter

from yosai_intel_dashboard.src.services.security import generate_service_jwt

router = APIRouter(prefix="/dev", tags=["dev"])


@router.get("/token")
def mint_dev_token() -> dict[str, str]:
    """Mint a short-lived JWT for development."""
    token = generate_service_jwt("dev")
    return {"access_token": token}
