"""Feature flag audit routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from yosai_intel_dashboard.src.services.feature_flags.audit import (
    get_feature_flag_audit_history,
)
from yosai_intel_dashboard.src.services.security import require_permission

router = APIRouter(prefix="/feature-flags", tags=["feature-flags"])


@router.get("/{name}/audit")
async def feature_flag_audit_history(
    name: str,
    limit: int = Query(100, ge=1, le=1000),
    _: None = Depends(require_permission("feature_flags.read")),
) -> JSONResponse:
    """Return audit history for a feature flag."""
    history = get_feature_flag_audit_history(name, limit)
    return JSONResponse({"flag": name, "history": history})
