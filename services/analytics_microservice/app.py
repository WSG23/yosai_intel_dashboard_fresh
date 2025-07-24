import logging
import time

from fastapi import (
    Depends,
    Header,
    HTTPException,
    status,
    APIRouter,
    UploadFile,
    File,
    Form,
)
from yosai_framework.service import BaseService
from shared.errors.types import ErrorCode
from yosai_framework.errors import ServiceError
from jose import jwt
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel
from pathlib import Path
import json

from config import get_database_config
from config.validate import validate_required_env
from services.analytics_microservice import async_queries
from services.common.async_db import close_pool, create_pool, get_pool


SERVICE_NAME = "analytics-microservice"
service = BaseService(SERVICE_NAME, "")
app = service.app

from services.common.secrets import get_secret

JWT_SECRET = get_secret("secret/data/jwt#secret")


def verify_token(authorization: str = Header("")) -> None:
    """Validate Authorization header using JWT_SECRET."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ServiceError(ErrorCode.UNAUTHORIZED, "unauthorized").to_dict(),
        )
    token = authorization.split(" ", 1)[1]
    try:
        claims = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ServiceError(ErrorCode.UNAUTHORIZED, "unauthorized").to_dict(),
        ) from exc
    exp = claims.get("exp")
    if exp is not None and exp < time.time():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ServiceError(ErrorCode.UNAUTHORIZED, "unauthorized").to_dict(),
        )
    if not claims.get("iss"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ServiceError(ErrorCode.UNAUTHORIZED, "unauthorized").to_dict(),
        )


class PatternsRequest(BaseModel):
    days: int = 7


@app.on_event("startup")
async def _startup() -> None:
    if not JWT_SECRET:
        raise RuntimeError("missing JWT secret")


    cfg = get_database_config()
    await create_pool(
        cfg.get_connection_string(),
        min_size=cfg.initial_pool_size,
        max_size=cfg.max_pool_size,
        timeout=cfg.connection_timeout,
    )

    # Redis or other dependencies would be initialized here
    app.state.model_dir = Path(os.environ.get("MODEL_DIR", "model_store"))
    app.state.model_dir.mkdir(parents=True, exist_ok=True)
    app.state.model_registry = {}
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
    service.stop()


@app.post("/api/v1/analytics/get_dashboard_summary")
async def dashboard_summary(_: None = Depends(verify_token)):
    pool = await get_pool()
    return await async_queries.fetch_dashboard_summary(pool)


@app.post("/api/v1/analytics/get_access_patterns_analysis")
async def access_patterns(req: PatternsRequest, _: None = Depends(verify_token)):
    pool = await get_pool()
    return await async_queries.fetch_access_patterns(pool, req.days)


models_router = APIRouter(prefix="/api/v1/models", tags=["models"])


@models_router.post("/register")
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
    meta = {"name": name, "version": version, "path": str(dest_path)}
    meta["active"] = True
    registry = app.state.model_registry.setdefault(name, [])
    for entry in registry:
        entry["active"] = False
    registry.append(meta)
    return meta


@models_router.get("/{name}")
async def list_versions(name: str, _: None = Depends(verify_token)):
    registry = app.state.model_registry.get(name)
    if not registry:
        raise HTTPException(status_code=404, detail="model not found")
    return {
        "name": name,
        "versions": [e["version"] for e in registry],
        "active_version": next((e["version"] for e in registry if e.get("active")), None),
    }


@models_router.post("/{name}/rollback")
async def rollback(name: str, version: str = Form(...), _: None = Depends(verify_token)):
    registry = app.state.model_registry.get(name)
    if not registry:
        raise HTTPException(status_code=404, detail="model not found")
    if version not in [e["version"] for e in registry]:
        raise HTTPException(status_code=404, detail="version not found")
    for entry in registry:
        entry["active"] = entry["version"] == version
    return {"name": name, "active_version": version}


app.include_router(models_router)


FastAPIInstrumentor.instrument_app(app)
Instrumentator().instrument(app).expose(app)


@app.on_event("startup")
async def _write_openapi() -> None:
    """Persist OpenAPI schema for docs."""
    docs_path = Path(__file__).resolve().parents[2] / "docs" / "analytics_microservice_openapi.json"
    docs_path.write_text(json.dumps(app.openapi(), indent=2))
