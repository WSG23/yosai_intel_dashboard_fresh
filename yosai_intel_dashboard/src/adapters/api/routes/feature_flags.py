from __future__ import annotations

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel

from yosai_intel_dashboard.src.services.feature_flags import feature_flags
from yosai_intel_dashboard.src.services.security import require_role

try:  # pragma: no cover - optional dependency
    from yosai_intel_dashboard.src.services import feature_flag_audit
except Exception:  # pragma: no cover - audit service may be absent
    feature_flag_audit = None

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/feature-flags", tags=["feature-flags"])


class FeatureFlag(BaseModel):
    name: str
    enabled: bool


class FeatureFlagUpdate(BaseModel):
    enabled: bool


class FeatureFlagAuditEntry(BaseModel):
    actor_user_id: str
    timestamp: datetime
    old_value: bool | None = None
    new_value: bool | None = None
    reason: str | None = None
    metadata: dict[str, Any] | None = None


class FeatureFlagAuditHistory(BaseModel):
    history: list[FeatureFlagAuditEntry]


# ---------------------------------------------------------------------------


def _persist_flags() -> None:
    """Persist current flags to the source file when possible."""
    source = feature_flags.source
    if source.startswith("http://") or source.startswith("https://"):
        return
    path = Path(source)
    try:
        path.write_text(json.dumps(feature_flags.get_all(), indent=2))
    except Exception as exc:  # pragma: no cover - best effort
        logger.warning("Failed to write feature flags: %s", exc)


@router.get("/")
async def list_feature_flags(_: None = Depends(require_role("user"))):
    """Return all feature flags."""
    return feature_flags.get_all()


@router.get("/{name}")
async def get_feature_flag(name: str, _: None = Depends(require_role("user"))):
    """Return a single feature flag by *name*."""
    flags = feature_flags.get_all()
    if name not in flags:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="flag not found"
        )
    return {"name": name, "enabled": flags[name]}


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_feature_flag(
    flag: FeatureFlag, _: None = Depends(require_role("admin"))
):
    """Create a new feature flag."""
    flags = feature_flags.get_all()
    if flag.name in flags:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="flag exists")
    feature_flags._flags[flag.name] = flag.enabled
    _persist_flags()
    return flag


@router.put("/{name}")
async def update_feature_flag(
    name: str, flag: FeatureFlagUpdate, _: None = Depends(require_role("admin"))
):
    """Update an existing feature flag."""
    if name not in feature_flags.get_all():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="flag not found"
        )
    feature_flags._flags[name] = flag.enabled
    _persist_flags()
    return {"name": name, "enabled": flag.enabled}


@router.delete("/{name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_feature_flag(name: str, _: None = Depends(require_role("admin"))):
    """Delete a feature flag."""
    if name not in feature_flags.get_all():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="flag not found"
        )
    del feature_flags._flags[name]
    _persist_flags()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{name}/audit", response_model=FeatureFlagAuditHistory)
async def get_feature_flag_audit(
    name: str, _: None = Depends(require_role("admin"))
) -> FeatureFlagAuditHistory:
    """Return audit history for a feature flag."""
    if feature_flag_audit is None or not hasattr(
        feature_flag_audit, "get_feature_flag_audit_history"
    ):
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="audit service unavailable",
        )
    history = feature_flag_audit.get_feature_flag_audit_history(name)
    return FeatureFlagAuditHistory(history=history)
