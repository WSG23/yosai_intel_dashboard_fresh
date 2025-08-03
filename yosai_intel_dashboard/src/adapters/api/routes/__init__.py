"""Additional API routers."""
from fastapi import APIRouter

from .feature_flags import router as feature_flags_router

router = APIRouter()
router.include_router(feature_flags_router)

__all__ = ["router", "feature_flags_router"]
