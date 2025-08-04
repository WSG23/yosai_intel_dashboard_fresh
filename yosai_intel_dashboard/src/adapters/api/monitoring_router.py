from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Query

from monitoring.request_metrics import model_monitoring_requests_total
from yosai_intel_dashboard.src.services.timescale.manager import TimescaleDBManager

# Expose routes without a version so the adapter can mount them under /v1 and
# also offer deprecated legacy access.
router = APIRouter(prefix="/model-monitoring", tags=["model-monitoring"])


@router.get("/{model_name}")
async def get_model_monitoring_events(
    model_name: str,
    start: Optional[datetime] = Query(None, description="Start of time range"),
    end: Optional[datetime] = Query(None, description="End of time range"),
) -> List[dict[str, Any]]:
    """Return monitoring events for a specific model.

    Optionally filter by ``start`` and ``end`` timestamps.
    """
    model_monitoring_requests_total.inc()
    manager = TimescaleDBManager()
    await manager.connect()
    assert manager.pool is not None

    parts = ["SELECT * FROM model_monitoring_events WHERE model_name = $1"]
    params: List[Any] = [model_name]
    if start is not None:
        params.append(start)
        parts.append(f"AND time >= ${len(params)}")
    if end is not None:
        params.append(end)
        parts.append(f"AND time <= ${len(params)}")
    parts.append("ORDER BY time DESC")
    query = " ".join(parts)

    rows = await manager.pool.fetch(query, *params)
    return [dict(r) for r in rows]
