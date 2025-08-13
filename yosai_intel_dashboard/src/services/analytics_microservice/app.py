from __future__ import annotations

"""Minimal FastAPI application for analytics microservice."""

from typing import Dict

from analytics import anomaly_detection, security_patterns
from yosai_intel_dashboard.models.ml.pipeline_contract import preprocess_events
from shared.errors.types import ErrorCode, ErrorResponse
from jose import jwt
from yosai_framework import ServiceBuilder
from yosai_intel_dashboard.models.ml import ModelRecord, ModelRegistry
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
from yosai_intel_dashboard.src.services.analytics_microservice.model_loader import (
    preload_active_models,
)
from yosai_intel_dashboard.src.services.analytics_microservice.unicode_middleware import (
    UnicodeSanitizationMiddleware,
)
from yosai_intel_dashboard.src.services.common.async_db import create_pool
from yosai_intel_dashboard.src.services.explainability_service import (
    ExplainabilityService,
)
from fastapi.responses import JSONResponse


from .analytics_service import AnalyticsService, get_analytics_service

app = FastAPI()


@app.on_event("startup")  # type: ignore[misc]

async def _startup() -> None:
    """Placeholder startup hook."""
    return None


@app.get("/api/v1/health")  # type: ignore[misc]
async def health() -> Dict[str, str]:
    """Basic service health endpoint."""
    return {"status": "ok"}


@app.get("/api/v1/analytics/dashboard-summary")  # type: ignore[misc]
async def dashboard_summary(

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


def _download_artifact(
    svc: AnalyticsService, name: str, record: ModelRecord
) -> Path:
    """Ensure the model artifact is present locally."""
    local_dir = Path(svc.model_dir) / name / record.version
    local_dir.mkdir(parents=True, exist_ok=True)
    local_path = local_dir / Path(record.storage_uri).name
    if not local_path.exists():
        try:
            svc.model_registry.download_artifact(record.storage_uri, str(local_path))
        except Exception as exc:  # noqa: BLE001
            raise http_error(ErrorCode.INTERNAL, str(exc), 500) from exc
    return local_path


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
