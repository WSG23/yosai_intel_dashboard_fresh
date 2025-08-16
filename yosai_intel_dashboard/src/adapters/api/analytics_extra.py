from __future__ import annotations

import csv
import io
import json

from fastapi import APIRouter, Depends, Response

from yosai_intel_dashboard.src.core import registry
from yosai_intel_dashboard.src.services.security import require_permission

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary")
def get_summary(_: None = Depends(require_permission("analytics.read"))):
    service = registry.get("cached_analytics_service")
    return service.get_analytics_summary_sync("default", "30d")


@router.get("/export")
def export_summary(_: None = Depends(require_permission("analytics.read"))):
    service = registry.get("cached_analytics_service")
    data = service.get_analytics_summary_sync("default", "30d")
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["key", "value"])
    for key, value in data.items():
        writer.writerow([key, json.dumps(value)])
    csv_content = buffer.getvalue()
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=summary.csv"},
    )
