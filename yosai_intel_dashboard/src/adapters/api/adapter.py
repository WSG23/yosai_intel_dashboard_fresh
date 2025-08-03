from __future__ import annotations

import asyncio
import base64
import os

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
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from itsdangerous import BadSignature, URLSafeTimedSerializer

from api.analytics_router import init_cache_manager
from api.analytics_router import router as analytics_router
from api.explanations import router as explanations_router
from api.monitoring_router import router as monitoring_router
from api.routes.feature_flags import router as feature_flags_router
from middleware.performance import TimingMiddleware
from yosai_framework.service import BaseService
from yosai_intel_dashboard.src.core.container import container
from yosai_intel_dashboard.src.core.rbac import create_rbac_service
from yosai_intel_dashboard.src.core.secrets_validator import validate_all_secrets
from yosai_intel_dashboard.src.infrastructure.config import get_security_config
from yosai_intel_dashboard.src.infrastructure.config.constants import API_PORT
from yosai_intel_dashboard.src.services.security import verify_service_jwt

bearer_scheme = HTTPBearer()


def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> None:
    """Validate Authorization header using JWT service tokens."""
    if not verify_service_jwt(credentials.credentials):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized"
        )


def create_api_app() -> "FastAPI":
    """Create API app registered on a BaseService."""
    validate_all_secrets()
    service = BaseService("api", "")
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
    build_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), os.pardir, "build")
    )

    settings = get_security_config()
    service.app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Initialize RBAC service
    try:
        service.app.state.rbac_service = asyncio.run(create_rbac_service())
    except Exception as exc:  # pragma: no cover - best effort
        service.log.error("Failed to initialize RBAC service: %s", exc)
        service.app.state.rbac_service = None

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

    # Helper dependency used for deprecated unversioned routes
    def add_deprecation_warning(response: Response) -> None:
        response.headers["Warning"] = (
            "299 - Deprecated API path; please use versioned '/v1' routes"
        )

    # Third-party analytics demo endpoints (FastAPI router)
    service.app.add_event_handler("startup", init_cache_manager)

    api_v1 = APIRouter(prefix="/v1")
    api_v1.include_router(analytics_router)
    api_v1.include_router(monitoring_router)
    api_v1.include_router(explanations_router)
    api_v1.include_router(feature_flags_router)

    service.app.include_router(api_v1, dependencies=[Depends(verify_token)])

    legacy_router = APIRouter()
    legacy_router.include_router(analytics_router)
    legacy_router.include_router(monitoring_router)
    legacy_router.include_router(explanations_router)
    legacy_router.include_router(feature_flags_router)

    service.app.include_router(
        legacy_router,
        dependencies=[Depends(verify_token), Depends(add_deprecation_warning)],
        deprecated=True,
    )

    # Core upload and related endpoints implemented directly with FastAPI
    file_processor = container.get("file_processor")
    file_handler = (
        container.get("file_handler") if container.has("file_handler") else None
    )

    serializer = URLSafeTimedSerializer(secret_key)

    from yosai_intel_dashboard.src.services.upload.upload_endpoint import (
        StatusSchema,
        UploadRequestSchema,
        UploadResponseSchema,
    )

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

    @service.app.post(
        "/v1/upload",
        response_model=UploadResponseSchema,
        status_code=202,
        dependencies=[Depends(verify_csrf)],
    )
    async def upload_files(
        payload: UploadRequestSchema,
        files: list[UploadFile] = File([]),
    ) -> dict:

        contents: list[str] = []
        filenames: list[str] = []
        validator = getattr(file_processor, "validator", None)
        if validator is None and file_handler is not None:
            validator = getattr(file_handler, "validator", None)
        if validator is None:
            from yosai_intel_dashboard.src.services.data_processing.file_handler import (
                FileHandler,
            )

            validator = FileHandler().validator

        if files:
            for upload in files:
                if not upload.filename:
                    continue
                file_bytes = await upload.read()
                try:
                    validator.validate_file_upload(upload.filename, file_bytes)
                except Exception:
                    raise HTTPException(status_code=400, detail="Invalid file")
                b64 = base64.b64encode(file_bytes).decode("utf-8", errors="replace")
                mime = upload.content_type or "application/octet-stream"
                contents.append(f"data:{mime};base64,{b64}")
                filenames.append(upload.filename)
        else:
            contents = payload.contents or []
            filenames = payload.filenames or []

        if not contents or not filenames:
            raise HTTPException(status_code=400, detail="No file provided")

        job_id = file_processor.process_file_async(contents[0], filenames[0])
        return {"job_id": job_id}

    @service.app.get("/v1/upload/status/{job_id}", response_model=StatusSchema)
    def upload_status(job_id: str) -> dict:
        status_data = file_processor.get_job_status(job_id)
        return {"status": status_data}

    # Settings endpoints
    from api.settings_endpoint import SettingsSchema, _load_settings, _save_settings

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

    # Token refresh endpoint
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

    # Serve React static files
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

    return service.app


if __name__ == "__main__":
    app = create_api_app()
    print("\n🚀 Starting Yosai Intel Dashboard API...")
    print(f"   Available at: http://localhost:{API_PORT}")
    print(f"   Upload endpoint: http://localhost:{API_PORT}/v1/upload")

    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=API_PORT)
