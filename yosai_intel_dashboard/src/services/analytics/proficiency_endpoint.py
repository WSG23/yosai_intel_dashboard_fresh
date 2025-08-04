from __future__ import annotations

from typing import Dict, List

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/proficiency", tags=["proficiency"])


class ProficiencyPayload(BaseModel):
    feature_usage: Dict[str, int] = {}
    dwell_time: Dict[str, float] = {}
    errors: List[str] = []


_metrics_store: List[ProficiencyPayload] = []


@router.post("/")
async def persist_metrics(payload: ProficiencyPayload) -> dict:
    """Persist proficiency metrics.

    In this minimal implementation metrics are kept in memory. In a real system
    this would store data in a database or analytics pipeline.
    """
    _metrics_store.append(payload)
    return {"status": "ok"}


@router.get("/")
async def list_metrics() -> List[ProficiencyPayload]:
    """Return collected metrics."""
    return _metrics_store
