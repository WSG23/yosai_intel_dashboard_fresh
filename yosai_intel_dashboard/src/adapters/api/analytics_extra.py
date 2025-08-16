from __future__ import annotations

from fastapi import APIRouter, Response

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary")
def analytics_summary() -> dict[str, object]:
    """Return a minimal analytics summary."""
    return {"total": 42, "trend": [1, 2, 3, 4, 5, 4, 6]}


@router.get("/export")
def export_csv() -> Response:
    """Return a static CSV export."""
    csv = "id,name,value\n1,Alice,10\n2,Bob,20\n3,Carol,30\n"
    return Response(
        content=csv,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=export.csv"},
    )
