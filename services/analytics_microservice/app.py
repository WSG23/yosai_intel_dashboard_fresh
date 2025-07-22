import os
import time

from fastapi import FastAPI, Depends, Header, HTTPException, status
from jose import jwt
from pydantic import BaseModel

from services.analytics_service import create_analytics_service

app = FastAPI(title="Analytics Microservice")
service = create_analytics_service()


def verify_token(authorization: str = Header("")) -> None:
    """Validate Authorization header using JWT_SECRET."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized"
        )
    token = authorization.split(" ", 1)[1]
    secret = os.getenv("JWT_SECRET", "")
    try:
        claims = jwt.decode(token, secret, algorithms=["HS256"])
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized"
        ) from exc
    exp = claims.get("exp")
    if exp is not None and exp < time.time():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized"
        )


class PatternsRequest(BaseModel):
    days: int = 7


@app.post("/api/v1/analytics/get_dashboard_summary")
async def dashboard_summary(_: None = Depends(verify_token)):
    return service.get_dashboard_summary()


@app.post("/api/v1/analytics/get_access_patterns_analysis")
async def access_patterns(req: PatternsRequest, _: None = Depends(verify_token)):
    return service.get_access_patterns_analysis(days=req.days)
