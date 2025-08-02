from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Query

from yosai_intel_dashboard.src.services.timescale.manager import TimescaleDBManager

router = APIRouter(prefix="/v1/model-monitoring", tags=["model-monitoring"])


@router.get("/{model_name}")
async def get_model_monitoring_events(
    model_name: str,
    start: Optional[datetime] = Query(None, description="Start of time range"),
    end: Optional[datetime] = Query(None, description="End of time range"),
) -> List[dict[str, Any]]:
    """Return monitoring events for a specific model.

    Optionally filter by ``start`` and ``end`` timestamps.
    """
    manager = TimescaleDBManager()
    await manager.connect()
    assert manager.pool is not None

    query = "SELECT * FROM model_monitoring_events WHERE model_name = $1"
    params: List[Any] = [model_name]
    if start is not None:
        params.append(start)
        query += f" AND time >= ${len(params)}"
    if end is not None:
        params.append(end)
        query += f" AND time <= ${len(params)}"
    query += " ORDER BY time DESC"

    rows = await manager.pool.fetch(query, *params)
    return [dict(r) for r in rows]
