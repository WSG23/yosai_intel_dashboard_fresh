from __future__ import annotations

import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
import redis.asyncio as aioredis
from fastapi import (
    APIRouter,
    Depends,
    FastAPI,
    File,
    Form,
    Header,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)
from services.auth import verify_jwt_token
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel
from yosai_intel_dashboard.models.ml import ModelRegistry
from yosai_intel_dashboard.src.infrastructure.discovery.health_check import (
    register_health_check,
    setup_health_checks,
)

from analytics import anomaly_detection, feature_extraction, security_patterns
from config import get_database_config
from config.config_loader import load_service_config
from core.security import RateLimiter
from services.analytics_microservice import async_queries
from services.analytics_microservice.unicode_middleware import (
    UnicodeSanitizationMiddleware,
)
from services.common import async_db
from services.common.async_db import close_pool, create_pool, get_pool
from services.common.secrets import get_secret
from shared.errors.types import ErrorCode
from yosai_framework import ServiceBuilder
from yosai_framework.errors import ServiceError
from yosai_framework.service import BaseService

SERVICE_NAME = "analytics-microservice"
service = (
    ServiceBuilder(SERVICE_NAME).with_logging().with_metrics("").with_health().build()
)
app = service.app
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(UnicodeSanitizationMiddleware)

rate_limiter = RateLimiter()


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    auth = request.headers.get("Authorization", "")
    identifier = (
        auth.split(" ", 1)[1] if auth.startswith("Bearer ") else request.client.host
    )
    result = rate_limiter.is_allowed(identifier or "anonymous", request.client.host)
    if not result["allowed"]:
        headers = {}
        retry = result.get("retry_after")
        if retry:
            headers["Retry-After"] = str(int(retry))
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "rate limit exceeded"},
            headers=headers,
        )
    return await call_next(request)


async def _db_check(_: FastAPI) -> bool:
    return await async_db.health_check()


register_health_check(app, "database", _db_check)

_SECRET_PATH = "secret/data/jwt#secret"


def _jwt_secret() -> str:
    """Return the current JWT secret."""
    return get_secret(_SECRET_PATH)


def verify_token(authorization: str = Header("")) -> dict:
    """Validate Authorization header and return JWT claims."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ServiceError(ErrorCode.UNAUTHORIZED, "unauthorized").to_dict(),
        )
    token = authorization.split(" ", 1)[1]
    return verify_jwt_token(token)


def preload_active_models() -> None:
    """Load active models from the registry into memory."""
    app.state.models = {}
    registry: ModelRegistry = app.state.model_registry
    try:
        records = registry.list_models()
    except Exception:  # pragma: no cover - registry unavailable
        return
    names = {r.name for r in records}
    for name in names:
        record = registry.get_model(name, active_only=True)
        if record is None:
            continue
        local_dir = app.state.model_dir / name / record.version
        local_dir.mkdir(parents=True, exist_ok=True)
        filename = os.path.basename(record.storage_uri)
        local_path = local_dir / filename
        if not local_path.exists():
            try:
                registry.download_artifact(record.storage_uri, str(local_path))
            except Exception:  # pragma: no cover - best effort
                continue
        try:
            model_obj = joblib.load(local_path)
            app.state.models[name] = model_obj
        except Exception:  # pragma: no cover - invalid model
            continue


class PatternsRequest(BaseModel):
    days: int = 7


class PredictRequest(BaseModel):
    data: Any


@app.on_event("startup")
async def _startup() -> None:
    # Ensure the JWT secret can be retrieved on startup
    _jwt_secret()

    cfg = get_database_config()
    await create_pool(
        cfg.get_connection_string(),
        min_size=cfg.initial_pool_size,
        max_size=cfg.max_pool_size,
        timeout=cfg.connection_timeout,
    )

    svc_cfg = load_service_config()
    app.state.redis = aioredis.from_url(svc_cfg.redis_url, decode_responses=True)
    app.state.cache_ttl = svc_cfg.cache_ttl

    app.state.model_dir = svc_cfg.model_dir
    app.state.model_dir.mkdir(parents=True, exist_ok=True)

    app.state.model_registry = ModelRegistry(
        svc_cfg.registry_db, svc_cfg.registry_bucket, mlflow_uri=svc_cfg.mlflow_uri
    )
    preload_active_models()
    app.state.ready = True
    app.state.startup_complete = True


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/health/live")
async def health_live() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok" if app.state.live else "shutdown"}


@app.get("/health/startup")
async def health_startup() -> dict[str, str]:
    """Startup probe."""
    if app.state.startup_complete:
        return {"status": "complete"}
    raise HTTPException(
        status_code=503,
        detail=ServiceError(ErrorCode.UNAVAILABLE, "starting").to_dict(),
    )


@app.get("/health/ready")
async def health_ready() -> dict[str, str]:
    """Readiness probe."""
    if app.state.ready:
        return {"status": "ready"}
    raise HTTPException(
        status_code=503,
        detail=ServiceError(ErrorCode.UNAVAILABLE, "not ready").to_dict(),
    )


@app.on_event("shutdown")
async def _shutdown() -> None:
    await close_pool()
    redis = getattr(app.state, "redis", None)
    if redis is not None:
        await redis.close()
    service.stop()


@app.get("/api/v1/analytics/dashboard-summary")
@rate_limit_decorator()
async def dashboard_summary(_: None = Depends(verify_token)):
    cache_key = "dashboard_summary"
    cached = await app.state.redis.get(cache_key)
    if cached:
        return json.loads(cached)
    pool = await get_pool()
    result = await async_queries.fetch_dashboard_summary(pool)
    await app.state.redis.set(cache_key, json.dumps(result), ex=app.state.cache_ttl)
    return result


@app.get("/api/v1/analytics/access-patterns")
@rate_limit_decorator()
async def access_patterns(days: int = Query(7), _: None = Depends(verify_token)):
    cache_key = f"access:{days}"

    cached = await app.state.redis.get(cache_key)
    if cached:
        return json.loads(cached)
    pool = await get_pool()
    result = await async_queries.fetch_access_patterns(pool, days)

    await app.state.redis.set(cache_key, json.dumps(result), ex=app.state.cache_ttl)
    return result


@app.post("/api/v1/analytics/threat_assessment")
async def threat_assessment(
    request: Request,
    file: UploadFile | None = File(None),
    _: None = Depends(verify_token),
):
    """Run threat assessment on raw intel data."""
    try:
        if file is not None:
            raw_bytes = await file.read()
            payload = json.loads(raw_bytes.decode("utf-8"))
        else:
            payload = await request.json()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail="invalid payload") from exc

    if isinstance(payload, list):
        df = pd.DataFrame(payload)
    elif isinstance(payload, dict) and "data" in payload:
        df = pd.DataFrame(payload["data"])
    else:
        df = pd.DataFrame(payload)

    features = feature_extraction.extract_event_features(df)
    anomaly = anomaly_detection.AnomalyDetector().analyze_anomalies(features)
    patterns = security_patterns.SecurityPatternsAnalyzer().analyze_security_patterns(
        features
    )

    ad_result = asdict(anomaly)
    sp_result = asdict(patterns)

    combined_risk = (
        ad_result.get("risk_assessment", {}).get("risk_score", 0.0)
        + sp_result.get("overall_score", 0.0) / 100
    ) / 2

    return {
        "anomaly_detection": ad_result,
        "security_patterns": sp_result,
        "combined_risk_score": combined_risk,
    }


models_router = APIRouter(prefix="/api/v1/models", tags=["models"])


@models_router.post("/register")
@rate_limit_decorator()
async def register_model(
    name: str = Form(...),
    version: str = Form(...),
    file: UploadFile = File(...),
    _: None = Depends(verify_token),
):
    dest_dir = app.state.model_dir / name / version
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / file.filename
    contents = await file.read()
    dest_path.write_bytes(contents)
    try:
        record = app.state.model_registry.register_model(
            name,
            str(dest_path),
            {},
            "",
            version=version,
        )
        app.state.model_registry.set_active_version(name, record.version)
        try:
            model_obj = joblib.load(dest_path)
            app.state.models[name] = model_obj
        except Exception:  # pragma: no cover - invalid model file
            pass
    except Exception as exc:  # pragma: no cover - registry failure
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"name": name, "version": record.version}


@models_router.get("/{name}")
@rate_limit_decorator()
async def list_versions(name: str, _: None = Depends(verify_token)):
    records = app.state.model_registry.list_models(name)
    if not records:
        raise HTTPException(status_code=404, detail="model not found")
    return {
        "name": name,
        "versions": [r.version for r in records],
        "active_version": next((r.version for r in records if r.is_active), None),
    }


@models_router.post("/{name}/rollback")
async def rollback(
    name: str, version: str = Form(...), _: None = Depends(verify_token)
):
    records = app.state.model_registry.list_models(name)
    if not records or version not in [r.version for r in records]:
        raise HTTPException(status_code=404, detail="version not found")
    try:
        app.state.model_registry.set_active_version(name, version)
    except Exception as exc:  # pragma: no cover - registry failure
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    preload_active_models()
    return {"name": name, "active_version": version}


@models_router.post("/{name}/predict")
@rate_limit_decorator()
async def predict(
    name: str,
    req: PredictRequest,
    _: None = Depends(verify_token),
):
    record = app.state.model_registry.get_model(name, active_only=True)
    if record is None:
        raise HTTPException(status_code=404, detail="no active version")
    local_dir = app.state.model_dir / name / record.version
    local_dir.mkdir(parents=True, exist_ok=True)
    local_path = local_dir / os.path.basename(record.storage_uri)
    if not local_path.exists():
        try:
            app.state.model_registry.download_artifact(
                record.storage_uri, str(local_path)
            )
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    model_obj = app.state.models.get(name)
    if model_obj is None:
        try:
            model_obj = joblib.load(local_path)
            app.state.models[name] = model_obj
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
    try:
        result = model_obj.predict(req.data)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    try:
        df = pd.DataFrame(req.data)
        app.state.model_registry.log_features(name, df)
    except Exception:
        pass
    return {"predictions": result}


@models_router.get("/{name}/drift")
@rate_limit_decorator()
async def get_drift(name: str, _: None = Depends(verify_token)):
    metrics = app.state.model_registry.get_drift_metrics(name)
    if not metrics:
        raise HTTPException(status_code=404, detail="no drift data")
    return metrics


app.include_router(models_router)


FastAPIInstrumentor.instrument_app(app)
Instrumentator().instrument(app).expose(app)
setup_health_checks(app)


@app.on_event("startup")
async def _write_openapi() -> None:
    """Persist OpenAPI schema for docs."""
    docs_path = (
        Path(__file__).resolve().parents[2]
        / "docs"
        / "analytics_microservice_openapi.json"
    )
    docs_path.write_text(json.dumps(app.openapi(), indent=2))
