from __future__ import annotations
from io import StringIO
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from yosai_intel_dashboard.src.core import registry
from yosai_intel_dashboard.src.services.security import require_permission

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/summary")
async def get_summary(_: None = Depends(require_permission("analytics.read"))):
    svc = registry.get("cached_analytics_service")
    data = svc.get_analytics_summary_sync("default", "30d")
    return JSONResponse(content=data)

@router.get("/export", response_class=StreamingResponse)
async def export_csv(_: None = Depends(require_permission("analytics.read"))):
    svc = registry.get("cached_analytics_service")
    data = svc.get_analytics_summary_sync("default", "30d")
    out = StringIO()
    out.write("metric,value\n")
    for k, v in (data.items() if isinstance(data, dict) else []):
        out.write(f"{k},{v}\n")
    out.seek(0)
    return StreamingResponse(out, media_type="text/csv", headers={"Content-Disposition":"attachment; filename=analytics.csv"})
