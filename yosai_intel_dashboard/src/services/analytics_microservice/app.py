from __future__ import annotations

import json
import os
import uuid
import logging
import time
import io
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict

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
    Query,
    Request,
    UploadFile,
    status,
)
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel, ConfigDict

from analytics import anomaly_detection, security_patterns
from yosai_intel_dashboard.models.ml.pipeline_contract import preprocess_events
from shared.errors.types import ErrorCode, ErrorResponse
from jose import jwt
from yosai_framework import ServiceBuilder
from yosai_intel_dashboard.models.ml import ModelRegistry
from yosai_intel_dashboard.src.core.security import RateLimiter, security_config
from yosai_intel_dashboard.src.database.utils import parse_connection_string
from yosai_intel_dashboard.src.error_handling import http_error
from yosai_intel_dashboard.src.error_handling.middleware import ErrorHandlingMiddleware
from yosai_intel_dashboard.src.infrastructure.config import get_database_config
from yosai_intel_dashboard.src.infrastructure.config.loader import (
    ConfigurationLoader,
)
from yosai_intel_dashboard.src.infrastructure.discovery.health_check import (
    register_health_check,
    setup_health_checks,
)
from yosai_intel_dashboard.src.services.analytics_microservice import async_queries
from yosai_intel_dashboard.src.services.analytics_microservice.analytics_service import (
    AnalyticsService,
    get_analytics_service,
)
from yosai_intel_dashboard.src.services.analytics_microservice.unicode_middleware import (
    UnicodeSanitizationMiddleware,
)
from yosai_intel_dashboard.src.services.common.async_db import create_pool
from yosai_intel_dashboard.src.services.explainability_service import (
    ExplainabilityService,
)
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

SERVICE_NAME = "analytics-microservice"
service = (
    ServiceBuilder(SERVICE_NAME).with_logging().with_metrics("").with_health().build()
)
app = service.app
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(UnicodeSanitizationMiddleware)

service_cfg = ConfigurationLoader().get_service_config()

# Configure a Redis backed rate limiter
redis_client = aioredis.from_url(service_cfg.redis_url)
rate_limiter = RateLimiter(redis_client, limit=100, window=60)


@app.on_event("startup")
async def _start_rate_limiter() -> None:
    rate_limiter.start_cleanup()


@app.on_event("shutdown")
async def _stop_rate_limiter() -> None:
    await rate_limiter.stop_cleanup()


ERROR_RESPONSES = {
    400: {"model": ErrorResponse, "description": "Bad Request"},
    401: {"model": ErrorResponse, "description": "Unauthorized"},
    404: {"model": ErrorResponse, "description": "Not Found"},
    500: {"model": ErrorResponse, "description": "Internal Server Error"},
}


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    auth = request.headers.get("Authorization", "")
    identifier = (
        auth.split(" ", 1)[1] if auth.startswith("Bearer ") else request.client.host
    )
    result = await rate_limiter.is_allowed(
        identifier or "anonymous", request.client.host
    )
    headers = {
        "X-RateLimit-Limit": str(result.get("limit", rate_limiter.max_requests)),
        "X-RateLimit-Remaining": str(result.get("remaining", 0)),
        "X-RateLimit-Reset": str(int(result.get("reset", 0))),
    }
    if not result["allowed"]:
        retry = result.get("retry_after")
        if retry is not None:
            headers["Retry-After"] = str(int(retry))
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "rate limit exceeded"},
            headers=headers,
        )
    response = await call_next(request)
    for key, value in headers.items():
        response.headers[key] = value
    return response


def rate_limit_decorator(*_: Any, **__: Any):
    """Placeholder rate limit decorator."""

    def decorator(func):
        return func

    return decorator


async def _external_api_check(_: FastAPI) -> Dict[str, Any]:
    return {"healthy": True, "circuit_breaker": "closed", "retries": 0}


register_health_check(app, "database", _db_check)
register_health_check(app, "message_broker", _broker_check)
register_health_check(app, "external_api", _external_api_check)


def _jwt_secret() -> str:
    """Return the current JWT secret."""
    secret_path = os.getenv("JWT_SECRET_PATH")
    return security_config.get_secret("JWT_SECRET_KEY", vault_key=secret_path)


def verify_token(authorization: str = Header("")) -> dict:
    """Validate Authorization header and return JWT claims."""
    if not authorization.startswith("Bearer "):
        raise http_error(
            ErrorCode.UNAUTHORIZED,
            "unauthorized",
            status.HTTP_401_UNAUTHORIZED,
        )
    token = authorization.split(" ", 1)[1]
    try:
        claims = jwt.decode(token, _jwt_secret(), algorithms=["HS256"])
    except Exception as exc:  # noqa: BLE001
        raise http_error(
            ErrorCode.UNAUTHORIZED,
            "unauthorized",
            status.HTTP_401_UNAUTHORIZED,
        ) from exc
    exp = claims.get("exp")
    if exp is not None and exp < time.time():
        raise http_error(
            ErrorCode.UNAUTHORIZED,
            "unauthorized",
            status.HTTP_401_UNAUTHORIZED,
        )
    if not claims.get("iss"):
        raise http_error(
            ErrorCode.UNAUTHORIZED,
            "unauthorized",
            status.HTTP_401_UNAUTHORIZED,
        )


def preload_active_models(service: AnalyticsService) -> None:
    """Load active models from the registry into memory."""
    service.models = {}
    registry: ModelRegistry = service.model_registry
    try:
        records = registry.list_models()
    except Exception:  # pragma: no cover - registry unavailable
        return
    names = {r.name for r in records}
    for name in names:
        record = registry.get_model(name, active_only=True)
        if record is None:
            continue
        local_dir = service.model_dir / name / record.version
        local_dir.mkdir(parents=True, exist_ok=True)
        filename = Path(record.storage_uri).name
        local_path = local_dir / filename
        if not local_path.exists():
            try:
                registry.download_artifact(record.storage_uri, str(local_path))
            except Exception:  # pragma: no cover - best effort
                continue
        try:
            model_obj = joblib.load(local_path)
            service.models[name] = model_obj
        except Exception:  # pragma: no cover - invalid model
            continue


class PatternsRequest(BaseModel):
    days: int = 7


class PredictRequest(BaseModel):
    data: Any

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"data": {"features": [0.1, 0.2, 0.3]}}]}
    )


@app.on_event("startup")
async def _startup() -> None:
    # Ensure the JWT secret can be retrieved on startup
    _jwt_secret()

    cfg = get_database_config()
    dsn = cfg.get_connection_string()
    parse_connection_string(dsn)
    pool = await create_pool(
        dsn,
        min_size=cfg.initial_pool_size,
        max_size=cfg.max_pool_size,
        timeout=cfg.connection_timeout,
    )

    redis = aioredis.from_url(service_cfg.redis_url, decode_responses=True)

    model_dir = Path(service_cfg.model_dir)
    model_dir.mkdir(parents=True, exist_ok=True)

    registry = ModelRegistry(
        service_cfg.registry_db,
        service_cfg.registry_bucket,
        mlflow_uri=service_cfg.mlflow_uri,
    )
    service_obj = AnalyticsService(
        redis,
        pool,
        registry,
        service_cfg,
    )
    service_obj.preload_active_models()
    app.state.analytics_service = service_obj

    app.state.ready = True
    app.state.startup_complete = True


@app.get("/api/v1/health")
async def health() -> dict[str, str]:
    """Basic service health indicator.

    Returns a simple payload showing the service is reachable and running.
    """
    return {"status": "ok"}


@app.get("/api/v1/health/live")
async def health_live() -> dict[str, str]:
    """Liveness probe.

    Indicates whether the process is alive by inspecting ``app.state.live``.
    """
    return {"status": "ok" if app.state.live else "shutdown"}


@app.get("/api/v1/health/startup")
async def health_startup() -> dict[str, str]:
    """Startup probe.

    Verifies the application finished initializing by checking
    ``app.state.startup_complete`` and returns appropriate status.
    """
    if app.state.startup_complete:
        return {"status": "complete"}
    raise http_error(
        ErrorCode.UNAVAILABLE,
        "starting",
        503,
    )


@app.get("/api/v1/health/ready")
async def health_ready() -> dict[str, str]:
    """Readiness probe.

    Confirms external dependencies are available by consulting ``app.state.ready``.
    Returns 503 while the service is still warming up.
    """
    if app.state.ready:
        return {"status": "ready"}
    raise http_error(
        ErrorCode.UNAVAILABLE,
        "not ready",
        503,
    )


@app.on_event("shutdown")
async def _shutdown() -> None:
    svc: AnalyticsService | None = getattr(app.state, "analytics_service", None)
    if svc is not None:
        await svc.close()
    service.stop()


@app.get("/api/v1/analytics/dashboard-summary", responses=ERROR_RESPONSES)
@rate_limit_decorator()
async def dashboard_summary(
    _: None = Depends(verify_token),
    svc: AnalyticsService = Depends(get_analytics_service),
):
    """Return overall dashboard metrics.

    Retrieves summary analytics, caches the result in Redis and reuses the cached
    value on subsequent requests.
    """
    cache_key = "dashboard_summary"
    cached = await svc.redis.get(cache_key)
    if cached:
        return json.loads(cached)
    result = await async_queries.fetch_dashboard_summary(svc.pool)
    await svc.redis.set(cache_key, json.dumps(result), ex=svc.cache_ttl)
    return result


@app.get("/api/v1/analytics/access-patterns", responses=ERROR_RESPONSES)
@rate_limit_decorator()
async def access_patterns(
    days: int = Query(7),
    _: None = Depends(verify_token),
    svc: AnalyticsService = Depends(get_analytics_service),
):
    """Retrieve access pattern analytics.

    Parameters:
    - **days**: Number of days to include when computing access trends.
    Caches responses in Redis keyed by the day window.
    """
    cache_key = f"access:{days}"

    cached = await svc.redis.get(cache_key)
    if cached:
        return json.loads(cached)
    result = await async_queries.fetch_access_patterns(svc.pool, days)

    await svc.redis.set(cache_key, json.dumps(result), ex=svc.cache_ttl)
    return result


@app.post("/api/v1/analytics/threat_assessment", responses=ERROR_RESPONSES)
async def threat_assessment(
    request: Request,
    file: UploadFile | None = File(None),
    _: None = Depends(verify_token),
):
    """Run threat assessment on raw intel data.

    Accepts either a JSON body or an uploaded file containing event records and
    computes anomaly detection and security pattern scores.
    """
    try:
        if file is not None:
            raw_bytes = await file.read()
            payload = json.loads(raw_bytes.decode("utf-8"))
        else:
            payload = await request.json()
    except Exception as exc:  # noqa: BLE001
        raise http_error(ErrorCode.INVALID_INPUT, "invalid payload", 400) from exc

    if isinstance(payload, list):
        df = pd.DataFrame(payload)
    elif isinstance(payload, dict) and "data" in payload:
        df = pd.DataFrame(payload["data"])
    else:
        df = pd.DataFrame(payload)

    features = preprocess_events(df)
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


@app.post("/api/v1/analytics/batch_predict", responses=ERROR_RESPONSES)
async def batch_predict(
    file: UploadFile = File(...),
    model: str | None = Query(None),
    _: None = Depends(verify_token),
    svc: AnalyticsService = Depends(get_analytics_service),
):
    """Generate predictions from a CSV upload.

    The uploaded file is parsed as CSV, transformed using
    :func:`preprocess_events`, and then passed to a loaded model for
    inference. If multiple models are loaded, a specific model can be
    selected via the optional ``model`` query parameter.
    """

    try:
        df = pd.read_csv(io.BytesIO(await file.read()))
    except Exception as exc:  # noqa: BLE001
        raise http_error(ErrorCode.INVALID_INPUT, "invalid csv", 400) from exc

    features = preprocess_events(df)

    model_obj = (
        svc.models.get(model) if model else next(iter(svc.models.values()), None)
    )
    if model_obj is None:
        raise http_error(ErrorCode.NOT_FOUND, "model not found", 404)

    try:
        preds = model_obj.predict(features)
    except Exception as exc:  # noqa: BLE001
        raise http_error(ErrorCode.INTERNAL, str(exc), 500) from exc

    if hasattr(preds, "tolist"):
        preds = preds.tolist()
    return {"predictions": preds}


models_router = APIRouter(prefix="/api/v1/models", tags=["models"])


@models_router.post("/register", responses=ERROR_RESPONSES)
@rate_limit_decorator()
async def register_model(
    name: str = Form(...),
    version: str = Form(...),
    file: UploadFile = File(...),
    _: None = Depends(verify_token),
    svc: AnalyticsService = Depends(get_analytics_service),
):
    """Register a new ML model version.

    Saves the uploaded artifact, records it in the model registry and loads the
    model into memory if possible.
    """
    dest_dir = svc.model_dir / name / version
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / file.filename
    contents = await file.read()
    dest_path.write_bytes(contents)
    try:
        record = svc.model_registry.register_model(
            name,
            str(dest_path),
            {},
            "",
            version=version,
        )
        svc.model_registry.set_active_version(name, record.version)
        try:
            model_obj = joblib.load(dest_path)
            svc.models[name] = model_obj
        except Exception:  # pragma: no cover - invalid model file
            pass
    except Exception as exc:  # pragma: no cover - registry failure
        raise http_error(ErrorCode.INTERNAL, str(exc), 500) from exc
    return {"name": name, "version": record.version}


@models_router.get("/{name}", responses=ERROR_RESPONSES)
@rate_limit_decorator()
async def list_versions(
    name: str,
    _: None = Depends(verify_token),
    svc: AnalyticsService = Depends(get_analytics_service),
):
    """List model versions.

    Returns all registered versions for the model along with the active one.
    """
    records = svc.model_registry.list_models(name)
    if not records:
        raise http_error(ErrorCode.NOT_FOUND, "model not found", 404)
    return {
        "name": name,
        "versions": [r.version for r in records],
        "active_version": next((r.version for r in records if r.is_active), None),
    }


@models_router.post("/{name}/rollback", responses=ERROR_RESPONSES)
async def rollback(
    name: str,
    version: str = Form(...),
    _: None = Depends(verify_token),
    svc: AnalyticsService = Depends(get_analytics_service),
):
    """Rollback to a previous model version.

    Activates the specified ``version`` and reloads model artifacts into memory.
    """
    records = svc.model_registry.list_models(name)
    if not records or version not in [r.version for r in records]:
        raise http_error(ErrorCode.NOT_FOUND, "version not found", 404)
    try:
        svc.model_registry.set_active_version(name, version)
    except Exception as exc:  # pragma: no cover - registry failure
        raise http_error(ErrorCode.INTERNAL, str(exc), 500) from exc

    preload_active_models(svc)
    return {"name": name, "active_version": version}


@models_router.post("/{name}/predict", responses=ERROR_RESPONSES)
@rate_limit_decorator()
async def predict(
    name: str,
    req: PredictRequest,
    _: None = Depends(verify_token),
    svc: AnalyticsService = Depends(get_analytics_service),
):
    """Generate predictions using an active model.

    Downloads the model artifact if necessary and logs input features before
    returning the model's predictions.
    """
    record = svc.model_registry.get_model(name, active_only=True)
    if record is None:
        raise http_error(ErrorCode.NOT_FOUND, "no active version", 404)
    local_dir = app.state.model_dir / name / record.version

    local_dir.mkdir(parents=True, exist_ok=True)
    local_path = local_dir / Path(record.storage_uri).name
    if not local_path.exists():
        try:
            svc.model_registry.download_artifact(record.storage_uri, str(local_path))
        except Exception as exc:
            raise http_error(ErrorCode.INTERNAL, str(exc), 500) from exc

def _load_model(svc: AnalyticsService, name: str, local_path: Path) -> Any:
    """Load a model from memory or disk."""
    model_obj = svc.models.get(name)
    if model_obj is not None:
        return model_obj
    try:
        model_obj = joblib.load(local_path)
    except Exception as exc:
        raise http_error(ErrorCode.INTERNAL, str(exc), 500) from exc
    svc.models[name] = model_obj
    return model_obj


def _run_prediction(model_obj: Any, data: Any) -> Any:
    """Execute model inference on ``data``."""
    try:
        return model_obj.predict(data)
    except Exception as exc:
        raise http_error(ErrorCode.INTERNAL, str(exc), 500) from exc


def _log_explainability(
    svc: AnalyticsService,
    name: str,
    model_obj: Any,
    data: Any,
    record: ModelRecord,
    prediction_id: str,
) -> None:
    """Log feature data and SHAP explanations if possible."""
    try:
        df = pd.DataFrame(data)
    except Exception as exc:  # pragma: no cover - defensive
        logger.debug("DataFrame creation failed: %s", exc)
        return
    try:
        svc.model_registry.log_features(name, df)
    except Exception as exc:  # pragma: no cover - best effort
        logger.debug("Feature logging failed: %s", exc)
    try:
        explainer = ExplainabilityService()
        explainer.register_model(name, model_obj, background_data=df)
        shap_vals = explainer.shap_values(name, df)
        if svc.model_registry:
            svc.model_registry.log_explanation(
                prediction_id,
                name,
                record.version,
                {"shap_values": shap_vals.tolist()},
            )
    except Exception as exc:  # pragma: no cover - best effort
        logger.debug("Explainability logging failed: %s", exc)


@models_router.post("/{name}/predict", responses=ERROR_RESPONSES)
@rate_limit_decorator()
async def predict(
    name: str,
    req: PredictRequest,
    _: None = Depends(verify_token),
    svc: AnalyticsService = Depends(get_analytics_service),
):
    """Generate predictions using an active model.

    Downloads the model artifact if necessary and logs input features before
    returning the model's predictions.
    """
    record = svc.model_registry.get_model(name, active_only=True)
    if record is None:
        raise http_error(ErrorCode.NOT_FOUND, "no active version", 404)

    local_path = _download_artifact(svc, name, record)
    model_obj = _load_model(svc, name, local_path)
    result = _run_prediction(model_obj, req.data)

    prediction_id = str(uuid.uuid4())
    _log_explainability(
        svc,
        name,
        model_obj,
        req.data,
        record,
        prediction_id,
    )
    return {"prediction_id": prediction_id, "predictions": result}


@models_router.get("/{name}/drift", responses=ERROR_RESPONSES)
@rate_limit_decorator()
async def get_drift(
    name: str,
    _: None = Depends(verify_token),
    svc: AnalyticsService = Depends(get_analytics_service),
):
    """Retrieve data drift metrics for a model.

    Returns drift statistics recorded in the model registry or a 404 if none
    exist.
    """
    metrics = svc.model_registry.get_drift_metrics(name)
    if not metrics:
        raise http_error(ErrorCode.NOT_FOUND, "no drift data", 404)
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
