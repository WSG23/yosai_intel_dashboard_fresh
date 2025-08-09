from __future__ import annotations

import base64
import os
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    FastAPI,
    File,
    HTTPException,
    Request,
    Response,
    UploadFile,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import FileResponse
from itsdangerous import BadSignature, URLSafeTimedSerializer
from prometheus_fastapi_instrumentator import Instrumentator

from middleware.performance import TimingMiddleware
from middleware.rate_limit import RateLimitMiddleware, RedisRateLimiter
from middleware.security_headers import SecurityHeadersMiddleware
from yosai_framework.service import BaseService
from yosai_intel_dashboard.src.adapters.api.analytics_router import (
    init_cache_manager,
)
from yosai_intel_dashboard.src.adapters.api.analytics_router import (
    router as analytics_router,
)
from yosai_intel_dashboard.src.adapters.api.explanations import (
    router as explanations_router,
)
from yosai_intel_dashboard.src.adapters.api.monitoring_router import (
    router as monitoring_router,
)
from yosai_intel_dashboard.src.adapters.api.routes.feature_flags import (
    router as feature_flags_router,
)
from yosai_intel_dashboard.src.core.container import container
from yosai_intel_dashboard.src.core.rbac import create_rbac_service
from yosai_intel_dashboard.src.core.secrets_validator import validate_all_secrets
from yosai_intel_dashboard.src.infrastructure.config import get_security_config
from yosai_intel_dashboard.src.infrastructure.config.constants import API_PORT
from yosai_intel_dashboard.src.infrastructure.config.app_config import UploadConfig
from yosai_intel_dashboard.src.services.upload.upload_endpoint import (
    ALLOWED_MIME_TYPES,
    UploadRequestSchema,
    UploadResponseSchema,
    stream_upload,
)
from yosai_intel_dashboard.src.infrastructure.monitoring.request_metrics import (
    upload_file_bytes,
    upload_files_total,
)
from yosai_intel_dashboard.src.services.auth import require_service_token


def _configure_app(service: BaseService) -> str:
    """Initialize the FastAPI app, base service and middleware."""
    service.app = FastAPI(
        title="Yosai Dashboard API",
        version="1.0.0",
        openapi_url="/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    service._add_health_routes()
    service.start()
    service.app.add_middleware(TimingMiddleware)

    import redis

    redis_client = redis.Redis.from_url(
        os.getenv("REDIS_URL", "redis://localhost:6379/0")
    )
    limiter = RedisRateLimiter(redis_client, {"default": {"limit": 100, "burst": 0}})
    service.app.add_middleware(RateLimitMiddleware, limiter=limiter)

    return os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, "build"))


def _setup_security(service: BaseService) -> tuple[URLSafeTimedSerializer, callable]:
    """Configure security middleware and services."""
    settings = get_security_config()
    service.app.add_middleware(SecurityHeadersMiddleware)
    service.app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    async def init_rbac_service() -> None:
        try:
            service.app.state.rbac_service = await create_rbac_service()
        except Exception as exc:  # pragma: no cover - best effort
            service.log.error("Failed to initialize RBAC service: %s", exc)
            service.app.state.rbac_service = None

    service.app.add_event_handler("startup", init_rbac_service)

    secret_key = os.getenv("SECRET_KEY")
    if not secret_key:
        try:  # pragma: no cover - best effort
            from yosai_intel_dashboard.src.services.common.secrets import get_secret

            secret_key = get_secret("SECRET_KEY")
        except Exception:
            secret_key = None
    if not secret_key:
        raise RuntimeError(
            "SECRET_KEY is not set; configure it via environment or Vault"
        )
    service.app.state.secret_key = secret_key
    serializer = URLSafeTimedSerializer(secret_key)

    def add_deprecation_warning(response: Response) -> None:
        response.headers["Warning"] = (
            "299 - Deprecated API path; please use versioned '/v1' routes"
        )

    return serializer, add_deprecation_warning


def _register_routes(
    service: BaseService, build_dir: str, add_deprecation_warning: callable
) -> None:
    """Register routers and static file handlers."""
    service.app.add_event_handler("startup", init_cache_manager)

    api_v1 = APIRouter(prefix="/v1")
    api_v1.include_router(analytics_router)
    api_v1.include_router(monitoring_router)
    api_v1.include_router(explanations_router)
    api_v1.include_router(feature_flags_router)
    service.app.include_router(api_v1, dependencies=[Depends(require_service_token)])

    legacy_router = APIRouter()
    legacy_router.include_router(analytics_router)
    legacy_router.include_router(monitoring_router)
    legacy_router.include_router(explanations_router)
    legacy_router.include_router(feature_flags_router)
    service.app.include_router(
        legacy_router,
        dependencies=[Depends(require_service_token), Depends(add_deprecation_warning)],
        deprecated=True,
    )

    @service.app.get("/", include_in_schema=False)
    def root_index() -> FileResponse:
        return FileResponse(os.path.join(build_dir, "index.html"))

    @service.app.get("/{path:path}", include_in_schema=False)
    def serve_static(path: str) -> FileResponse:
        full_path = os.path.join(build_dir, path)
        if os.path.exists(full_path) and os.path.isfile(full_path):
            return FileResponse(full_path)
        return FileResponse(os.path.join(build_dir, "index.html"))

    def custom_openapi() -> dict:
        if service.app.openapi_schema:
            return service.app.openapi_schema
        schema = get_openapi(
            title=service.app.title,
            version="0.1.0",
            routes=service.app.routes,
        )
        components = schema.setdefault("components", {})
        security = components.setdefault("securitySchemes", {})
        security["HTTPBearer"] = {"type": "http", "scheme": "bearer"}
        for path in schema.get("paths", {}).values():
            for method in path.values():
                method.setdefault("security", [{"HTTPBearer": []}])
        service.app.openapi_schema = schema
        return schema

    service.app.openapi = custom_openapi
    Instrumentator().instrument(service.app).expose(service.app)


def _register_upload_endpoints(
    service: BaseService, serializer: URLSafeTimedSerializer
) -> None:
    """Register upload, settings and token refresh endpoints."""
    file_handler = (
        container.get("file_handler") if container.has("file_handler") else None
    )

    @service.app.middleware("http")
    async def enforce_csrf(request: Request, call_next):
        if request.method not in {"GET", "HEAD", "OPTIONS", "TRACE"}:
            token = (
                request.headers.get("X-CSRFToken")
                or request.headers.get("X-CSRF-Token")
                or request.cookies.get("csrf_token")
            )
            if not token:
                raise HTTPException(status_code=400, detail="Missing CSRF token")
            try:
                serializer.loads(token, max_age=3600)
            except BadSignature:
                raise HTTPException(status_code=400, detail="Invalid CSRF token")
        return await call_next(request)


    @service.app.get("/v1/csrf-token")
    def get_csrf_token(response: Response) -> dict:
        token = serializer.dumps("csrf")
        response.set_cookie("csrf_token", token, httponly=True)
        return {"csrf_token": token}

    def verify_csrf(request: Request) -> None:
        token = (
            request.headers.get("X-CSRFToken")
            or request.headers.get("X-CSRF-Token")
            or request.cookies.get("csrf_token")
        )
        if not token:
            raise HTTPException(status_code=400, detail="Missing CSRF token")
        try:
            serializer.loads(token, max_age=3600)
        except BadSignature:
            raise HTTPException(status_code=400, detail="Invalid CSRF token")

    cfg = UploadConfig()

    @service.app.post(
        "/v1/upload",
        response_model=UploadResponseSchema,
        status_code=200,
        dependencies=[Depends(verify_csrf)],
    )
    async def upload_files(
        payload: UploadRequestSchema,
        files: list[UploadFile] = File([]),
    ) -> dict:
        validator = None
        if file_handler is not None:
            validator = getattr(file_handler, "validator", None)
        if validator is None:
            from yosai_intel_dashboard.src.services.data_processing.file_handler import (
                FileHandler,
            )

            validator = FileHandler().validator

        results: list[dict[str, str]] = []
        storage_dir = Path(cfg.folder)

        if files:
            for upload in files:
                if not upload.filename:
                    continue
                data = await upload.read()
                mime = upload.content_type or "application/octet-stream"
                upload_files_total.inc()
                upload_file_bytes.observe(len(data))
                if mime not in ALLOWED_MIME_TYPES:
                    raise HTTPException(status_code=400, detail="Invalid file type")
                try:
                    res = validator.validate_file_upload(upload.filename, data)
                    if not res.valid:
                        raise ValueError(", ".join(res.issues or []))
                except Exception:
                    raise HTTPException(status_code=400, detail="Invalid file")
                if len(data) > cfg.max_file_size_bytes:
                    raise HTTPException(status_code=400, detail="File too large")
                dest = stream_upload(storage_dir, upload.filename, data)
                results.append({"filename": upload.filename, "path": str(dest)})
        else:
            contents = payload.contents or []
            filenames = payload.filenames or []
            for content, name in zip(contents, filenames):
                if "," not in content:
                    raise HTTPException(status_code=400, detail="Invalid file")
                header, b64data = content.split(",", 1)
                mime = header.split(";")[0].replace("data:", "", 1)
                if mime not in ALLOWED_MIME_TYPES:
                    raise HTTPException(status_code=400, detail="Invalid file type")
                try:
                    data = base64.b64decode(b64data)
                except Exception:
                    raise HTTPException(status_code=400, detail="Invalid file")
                try:
                    res = validator.validate_file_upload(name, data)
                    if not res.valid:
                        raise ValueError(", ".join(res.issues or []))
                except Exception:
                    raise HTTPException(status_code=400, detail="Invalid file")
                if len(data) > cfg.max_file_size_bytes:
                    raise HTTPException(status_code=400, detail="File too large")
                dest = stream_upload(storage_dir, name, data)
                results.append({"filename": name, "path": str(dest)})

        if not results:
            raise HTTPException(status_code=400, detail="No file provided")

        return {"results": results}

    from yosai_intel_dashboard.src.adapters.api.settings_endpoint import (
        SettingsSchema,
        _load_settings,
        _save_settings,
    )

    @service.app.get("/v1/settings", response_model=SettingsSchema)
    def get_settings() -> dict:
        return _load_settings()

    @service.app.post("/v1/settings", response_model=SettingsSchema)
    @service.app.put("/v1/settings", response_model=SettingsSchema)
    def update_settings(payload: SettingsSchema) -> dict:
        settings_data = _load_settings()
        settings_data.update(payload.dict(exclude_none=True))
        try:
            _save_settings(settings_data)
        except Exception as exc:  # pragma: no cover - defensive
            raise HTTPException(status_code=500, detail=str(exc))
        return settings_data

    from yosai_intel_dashboard.src.services.security import refresh_access_token
    from yosai_intel_dashboard.src.services.token_endpoint import (
        AccessTokenResponse,
        RefreshRequest,
    )

    @service.app.post(
        "/v1/token/refresh", response_model=AccessTokenResponse, status_code=200
    )
    def refresh_token(payload: RefreshRequest) -> dict:
        new_token = refresh_access_token(payload.refresh_token)
        if not new_token:
            raise HTTPException(status_code=401, detail="invalid refresh token")
        return {"access_token": new_token}


def create_api_app() -> "FastAPI":
    """Create API app registered on a BaseService."""
    validate_all_secrets()
    service = BaseService("api", "")
    build_dir = _configure_app(service)
    serializer, add_deprecation_warning = _setup_security(service)
    _register_routes(service, build_dir, add_deprecation_warning)
    _register_upload_endpoints(service, serializer)
    return service.app


if __name__ == "__main__":
    app = create_api_app()
    print("\n🚀 Starting Yosai Intel Dashboard API...")
    print(f"   Available at: http://localhost:{API_PORT}")
    print(f"   Upload endpoint: http://localhost:{API_PORT}/v1/upload")

    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=API_PORT)
