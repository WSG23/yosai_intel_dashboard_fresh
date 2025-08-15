from __future__ import annotations

from typing import Dict

from fastapi import APIRouter
from pydantic import BaseModel

from yosai_intel_dashboard.src.services.model_service import ModelService


class PredictRequest(BaseModel):
    value: float


class RolloutRequest(BaseModel):
    rollout: Dict[str, float]


def create_model_router(service: ModelService) -> APIRouter:
    router = APIRouter(prefix="/models", tags=["models"])

    @router.post("/{model_name}/predict")
    async def predict(model_name: str, req: PredictRequest) -> Dict[str, float | str]:
        model, version = service.get_model(model_name)
        result = model(req.value)
        return {"version": version, "result": result}

    @router.post("/{model_name}/v{version}/predict")
    async def predict_version(
        model_name: str, version: str, req: PredictRequest
    ) -> Dict[str, float | str]:
        model, _ = service.get_model(model_name, version)
        result = model(req.value)
        return {"version": version, "result": result}

    @router.post("/{model_name}/rollout")
    async def update_rollout(model_name: str, req: RolloutRequest) -> Dict[str, str]:
        service.set_rollout(model_name, req.rollout)
        meta = service.metadata(model_name)
        return {"status": "ok", "active": meta.get("active", "")}

    @router.get("/{model_name}/active")
    async def get_active(model_name: str) -> Dict[str, str]:
        meta = service.metadata(model_name)
        return {"version": meta.get("active", "")}

    return router

