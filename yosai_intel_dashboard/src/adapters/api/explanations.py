from fastapi import APIRouter, Depends

from shared.errors.types import ErrorCode
from yosai_intel_dashboard.src.error_handling import http_error
from yosai_intel_dashboard.src.services.security import require_permission
from yosai_intel_dashboard.src.services.analytics.analytics_service import (
    AnalyticsService,
    get_analytics_service,
)

router = APIRouter(prefix="/api/v1/explanations", tags=["explanations"])


@router.get("/{prediction_id}")
async def get_explanation(
    prediction_id: str,
    _: None = Depends(require_permission("analytics.read")),
    svc: AnalyticsService = Depends(get_analytics_service),
):
    """Return stored SHAP explanations for a prediction."""
    if svc.model_registry is None:
        raise http_error(ErrorCode.INTERNAL, "model registry unavailable", 500)
    record = svc.model_registry.get_explanation(prediction_id)
    if record is None:
        raise http_error(ErrorCode.NOT_FOUND, "explanation not found", 404)
    return record
