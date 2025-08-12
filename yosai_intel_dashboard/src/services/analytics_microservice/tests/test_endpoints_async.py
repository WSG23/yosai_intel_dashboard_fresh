from __future__ import annotations

import importlib.util
import os
import pathlib
import sys
import time
import types
from dataclasses import dataclass
from unittest.mock import AsyncMock

import httpx
import joblib
import pytest
from fastapi import FastAPI
from jose import jwt

SERVICES_PATH = pathlib.Path(__file__).resolve().parents[2]


class Dummy:
    def predict(self, data):
        return [len(data)]


# stub out the heavy 'services' package before pytest imports it
services_stub = types.ModuleType("services")
services_stub.__path__ = [str(SERVICES_PATH)]
sys.modules["services"] = services_stub


def load_app(jwt_secret: str | None = "secret") -> tuple:

    otel_stub = types.ModuleType("opentelemetry.instrumentation.fastapi")
    otel_stub.FastAPIInstrumentor = types.SimpleNamespace(
        instrument_app=lambda *a, **k: None
    )
    sys.modules.setdefault("opentelemetry.instrumentation.fastapi", otel_stub)

    prom_stub = types.ModuleType("prometheus_fastapi_instrumentator")

    class DummyInstr:
        def instrument(self, app):
            return self

        def expose(self, app):
            return self

    prom_stub.Instrumentator = lambda: DummyInstr()
    sys.modules.setdefault("prometheus_fastapi_instrumentator", prom_stub)

    import builtins

    builtins.ErrorHandlingMiddleware = lambda app, *a, **k: app
    builtins.rate_limit_decorator = lambda *a, **k: (lambda func: func)

    db_stub = types.ModuleType("services.common.async_db")
    db_stub.create_pool = AsyncMock()
    db_stub.close_pool = AsyncMock()
    db_stub.get_pool = AsyncMock(return_value=object())
    sys.modules["services.common.async_db"] = db_stub
    common_pkg = types.ModuleType("services.common")
    common_pkg.async_db = db_stub
    sys.modules["services.common"] = common_pkg

    config_stub = types.ModuleType("config")

    class _Cfg:
        def __init__(self):
            self.type = "sqlite"
            self.host = "localhost"
            self.port = 5432
            self.name = "test"
            self.user = "user"
            self.password = ""
            self.connection_timeout = 1

        def get_connection_string(self):
            return "postgresql://"

        initial_pool_size = 1
        max_pool_size = 1

    config_stub.DatabaseSettings = _Cfg
    config_stub.get_database_config = lambda: _Cfg()
    dynamic_module = types.ModuleType("config.dynamic_config")
    dynamic_module.dynamic_config = {}
    sys.modules["config.dynamic_config"] = dynamic_module
    base_module = types.ModuleType("config.base")
    base_module.CacheConfig = lambda *a, **k: None
    sys.modules["config.base"] = base_module
    db_exc_module = types.ModuleType("config.database_exceptions")

    class _UnicodeErr(Exception):
        def __init__(self, *a, **k):
            pass

    db_exc_module.UnicodeEncodingError = _UnicodeErr
    sys.modules["config.database_exceptions"] = db_exc_module
    sys.modules["config"] = config_stub

    env_stub = types.ModuleType("config.environment")
    env_stub.get_environment = lambda: "test"
    sys.modules["config.environment"] = env_stub

    validate_stub = types.ModuleType("config.validate")
    validate_stub.validate_required_env = lambda vars: None
    sys.modules["config.validate"] = validate_stub

    yf_config_stub = types.ModuleType("yosai_framework.config")

    class DummyCfg:
        service_name = "analytics-test"
        log_level = "INFO"
        metrics_addr = ""
        tracing_endpoint = ""

    yf_config_stub.ServiceConfig = DummyCfg
    yf_config_stub.load_config = lambda path: DummyCfg()
    sys.modules["yosai_framework.config"] = yf_config_stub

    redis_stub = types.ModuleType("redis")
    redis_async = types.ModuleType("redis.asyncio")
    redis_async.Redis = AsyncMock
    redis_stub.asyncio = redis_async
    sys.modules.setdefault("redis", redis_stub)
    sys.modules.setdefault("redis.asyncio", redis_async)

    analytics_stub = types.ModuleType(
        "services.analytics_microservice.analytics_service"
    )

    class DummyAnalyticsService:
        def __init__(self, *a, **k):
            self.redis = types.SimpleNamespace(get=AsyncMock(), set=AsyncMock())
            self.pool = object()
            self.model_registry = None
            self.cache_ttl = 300
            self.model_dir = pathlib.Path("/tmp")
            self.models = {}

        async def close(self):
            pass

        def preload_active_models(self):
            pass

    dummy_service = DummyAnalyticsService()

    analytics_stub.AnalyticsService = DummyAnalyticsService
    analytics_stub.get_analytics_service = lambda *a, **k: dummy_service
    sys.modules["services.analytics_microservice.analytics_service"] = analytics_stub

    queries_stub = types.ModuleType("services.analytics_microservice.async_queries")
    queries_stub.fetch_dashboard_summary = AsyncMock(return_value={"status": "ok"})
    queries_stub.fetch_access_patterns = AsyncMock(return_value={"days": 7})
    sys.modules["services.analytics_microservice.async_queries"] = queries_stub

    health_stub = types.ModuleType(
        "yosai_intel_dashboard.src.infrastructure.discovery.health_check"
    )
    health_stub.register_health_check = lambda *a, **k: None
    health_stub.setup_health_checks = lambda app: None
    health_stub.DependencyHealthMiddleware = lambda app: app
    sys.modules["yosai_intel_dashboard.src.infrastructure.discovery.health_check"] = (
        health_stub
    )

    service_stub = types.ModuleType("yosai_framework.service")

    class DummyService:
        def __init__(self):
            self.app = FastAPI()
            self.app.state.live = True
            self.app.state.ready = True
            self.app.state.startup_complete = True

        def stop(self):
            pass

    class DummyBuilder:
        def __init__(self, name: str):
            self

        def with_logging(self, *a, **k):
            return self

        def with_metrics(self, *a, **k):
            return self

        def with_health(self):
            return self

        def build(self):
            return DummyService()

    service_stub.BaseService = DummyService
    service_stub.ServiceBuilder = DummyBuilder
    sys.modules["yosai_framework.service"] = service_stub
    yf_pkg = types.ModuleType("yosai_framework")
    yf_pkg.ServiceBuilder = DummyBuilder
    yf_pkg.BaseService = DummyService
    errors_stub = types.ModuleType("yosai_framework.errors")

    class ServiceError(Exception):
        pass

    errors_stub.ServiceError = ServiceError
    sys.modules["yosai_framework"] = yf_pkg
    sys.modules["yosai_framework.errors"] = errors_stub

    secrets_stub = types.ModuleType("services.common.secrets")
    secrets_stub.get_secret = lambda path: "secret"
    sys.modules["services.common.secrets"] = secrets_stub

    auth_stub = types.ModuleType("services.auth")
    auth_stub.verify_jwt_token = lambda token: jwt.decode(
        token, jwt_secret, algorithms=["HS256"]
    )
    sys.modules["services.auth"] = auth_stub

    # Stub ModelRegistry used by the microservice
    registry_mod = types.ModuleType("models.ml.model_registry")

    @dataclass
    class DummyRecord:
        name: str
        version: str
        storage_uri: str
        is_active: bool = False

    class DummyRegistry:
        def __init__(self, *a, **k):
            self.models: dict[str, dict[str, DummyRecord]] = {}

        def register_model(
            self,
            name: str,
            model_path: str,
            metrics: dict,
            dataset_hash: str,
            *,
            version: str | None = None,
            training_date: None | object = None,
        ) -> DummyRecord:
            rec = DummyRecord(name, version or "1", model_path)
            self.models.setdefault(name, {})[rec.version] = rec
            return rec

        def set_active_version(self, name: str, version: str) -> None:
            for r in self.models.get(name, {}).values():
                r.is_active = r.version == version

        def get_model(
            self,
            name: str,
            version: str | None = None,
            *,
            active_only: bool = False,
        ) -> DummyRecord | None:
            if active_only:
                for r in self.models.get(name, {}).values():
                    if r.is_active:
                        return r
                return None
            if version:
                return self.models.get(name, {}).get(version)
            return None

        def list_models(self, name: str | None = None):
            if name:
                return list(self.models.get(name, {}).values())
            res = []
            for d in self.models.values():
                res.extend(d.values())
            return res

        def download_artifact(self, src: str, dest: str) -> None:
            Path(dest).write_bytes(Path(src).read_bytes())

    registry_mod.ModelRegistry = DummyRegistry
    registry_mod.ModelRecord = DummyRecord
    sys.modules["models.ml.model_registry"] = registry_mod
    sys.modules["yosai_intel_dashboard.models.ml.model_registry"] = registry_mod
    ml_pkg = types.ModuleType("models.ml")
    ml_pkg.ModelRegistry = DummyRegistry
    ml_pkg.ModelRecord = DummyRecord
    sys.modules["models.ml"] = ml_pkg
    sys.modules["yosai_intel_dashboard.models.ml"] = ml_pkg
    models_stub = types.ModuleType("models")
    models_stub.ml = ml_pkg
    sys.modules["models"] = models_stub
    sys.modules["yosai_intel_dashboard.models"] = models_stub

    # Stub analytics modules used by threat_assessment endpoint
    fe_stub = types.ModuleType("analytics.feature_extraction")
    fe_stub.extract_event_features = lambda df, logger=None: df

    ad_stub = types.ModuleType("analytics.anomaly_detection")

    @dataclass
    class DummyResult:
        total_anomalies: int = 0
        severity_distribution: dict = None
        detection_summary: dict = None
        risk_assessment: dict = None
        recommendations: list = None
        processing_metadata: dict = None

    class DummyDetector:
        def analyze_anomalies(self, df):
            return DummyResult(
                severity_distribution={},
                detection_summary={},
                risk_assessment={"risk_score": 0},
                recommendations=[],
                processing_metadata={},
            )

    ad_stub.AnomalyDetector = DummyDetector

    sp_stub = types.ModuleType("analytics.security_patterns")

    @dataclass
    class DummyAssessment:
        overall_score: int = 0
        risk_level: str = "low"
        confidence_interval: tuple = (0.0, 0.0)
        threat_indicators: list = None
        pattern_analysis: dict = None
        recommendations: list = None

    class DummyAnalyzer:
        def analyze_security_patterns(self, df):
            return DummyAssessment(
                threat_indicators=[],
                pattern_analysis={},
                recommendations=[],
            )

    sp_stub.SecurityPatternsAnalyzer = DummyAnalyzer

    analytics_pkg = types.ModuleType("analytics")
    analytics_pkg.feature_extraction = fe_stub
    analytics_pkg.anomaly_detection = ad_stub
    analytics_pkg.security_patterns = sp_stub
    sys.modules["analytics"] = analytics_pkg
    sys.modules["analytics.feature_extraction"] = fe_stub
    sys.modules["analytics.anomaly_detection"] = ad_stub
    sys.modules["analytics.security_patterns"] = sp_stub

    # Minimal stubs for unicode and validation utilities
    core_unicode = types.ModuleType("core.unicode")
    core_unicode.sanitize_for_utf8 = lambda x: x
    core_pkg = types.ModuleType("core")
    core_pkg.unicode = core_unicode
    security_stub = types.ModuleType("core.security")

    class DummyRateLimiter:
        def is_allowed(self, *a, **k):
            return {"allowed": True}

    security_stub.RateLimiter = DummyRateLimiter
    core_pkg.security = security_stub
    sys.modules["core"] = core_pkg
    sys.modules["core.unicode"] = core_unicode
    sys.modules["core.security"] = security_stub

    unicode_stub = types.ModuleType("utils.unicode_handler")

    class DummyHandler:
        @staticmethod
        def sanitize(obj):
            return obj

    unicode_stub.UnicodeHandler = DummyHandler
    sys.modules["utils.unicode_handler"] = unicode_stub

    val_stub = types.ModuleType("validation.unicode_validator")

    class DummyValidator:
        def validate_dataframe(self, df):
            return df

    val_stub.UnicodeValidator = DummyValidator
    sys.modules["validation.unicode_validator"] = val_stub

    sys.modules.setdefault("tracing", types.ModuleType("tracing"))
    sys.modules.setdefault("hvac", types.ModuleType("hvac"))

    if jwt_secret is not None:
        os.environ["JWT_SECRET_KEY"] = jwt_secret
    else:
        os.environ.pop("JWT_SECRET_KEY", None)

    spec = importlib.util.spec_from_file_location(
        "services.analytics_microservice.app",
        SERVICES_PATH / "analytics_microservice" / "app.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[arg-type]

    # Mark application as ready without running full startup
    module.app.state.ready = True
    module.app.state.startup_complete = True
    module.app.state.analytics_service = dummy_service

    # base service already registers health routes

    return module, queries_stub, dummy_service


@pytest.mark.asyncio
async def test_health_endpoints():
    module, _, _ = load_app()
    transport = httpx.ASGITransport(app=module.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

        resp = await client.get("/api/v1/health/live")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

        resp = await client.get("/api/v1/health/startup")
        assert resp.status_code == 200
        assert resp.json() == {"status": "complete"}

        resp = await client.get("/api/v1/health/ready")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ready"}


@pytest.mark.asyncio
async def test_dashboard_summary_endpoint():
    module, queries_stub, dummy_service = load_app()

    token = jwt.encode(
        {"sub": "svc", "iss": "gateway", "exp": int(time.time()) + 60},
        "secret",
        algorithm="HS256",
    )
    assert verify_jwt_token(token)["iss"] == "gateway"
    headers = {"Authorization": f"Bearer {token}"}

    transport = httpx.ASGITransport(app=module.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/analytics/dashboard-summary", headers=headers)

        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

    queries_stub.fetch_dashboard_summary.assert_awaited_once()


@pytest.mark.asyncio
async def test_unauthorized_request():
    module, _, _ = load_app()
    transport = httpx.ASGITransport(app=module.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/analytics/dashboard-summary")
        assert resp.status_code == 401
        assert resp.json() == {
            "detail": {"code": "unauthorized", "message": "unauthorized"}
        }


@pytest.mark.asyncio
async def test_internal_error_response():
    module, queries_stub, _ = load_app()
    from yosai_intel_dashboard.src.services.auth import verify_jwt_token

    queries_stub.fetch_dashboard_summary.side_effect = RuntimeError("boom")
    token = jwt.encode(
        {"sub": "svc", "iss": "gateway", "exp": int(time.time()) + 60},
        "secret",
        algorithm="HS256",
    )
    assert verify_jwt_token(token)["iss"] == "gateway"
    headers = {"Authorization": f"Bearer {token}"}

    transport = httpx.ASGITransport(app=module.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/api/v1/analytics/dashboard-summary",
            headers=headers,
        )
        assert resp.status_code == 500
        assert resp.json() == {"code": "internal", "message": "boom"}


@pytest.mark.asyncio
async def test_model_registry_endpoints(tmp_path):
    module, _, svc = load_app()
    svc.model_dir = tmp_path
    from yosai_intel_dashboard.models.ml import ModelRegistry

    svc.model_registry = ModelRegistry()

    token = jwt.encode(
        {"sub": "svc", "iss": "gateway", "exp": int(time.time()) + 60},
        "secret",
        algorithm="HS256",
    )
    assert verify_jwt_token(token)["iss"] == "gateway"
    headers = {"Authorization": f"Bearer {token}"}

    transport = httpx.ASGITransport(app=module.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        files = {"file": ("model.bin", b"data")}
        data = {"name": "demo", "version": "1"}
        resp = await client.post(
            "/api/v1/models/register", headers=headers, data=data, files=files
        )
        assert resp.status_code == 200
        assert resp.json()["version"] == "1"

        resp = await client.get("/api/v1/models/demo", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["versions"] == ["1"]

        resp = await client.post(
            "/api/v1/models/demo/rollback",
            headers=headers,
            data={"version": "1"},
        )
        assert resp.status_code == 200
        assert resp.json()["active_version"] == "1"


@pytest.mark.asyncio
async def test_predict_endpoint(tmp_path):
    module, _, svc = load_app()
    svc.model_dir = tmp_path

    model = Dummy()
    path = tmp_path / "demo" / "1" / "model.joblib"
    path.parent.mkdir(parents=True)
    joblib.dump(model, path)
    from yosai_intel_dashboard.models.ml import ModelRegistry

    registry = ModelRegistry()
    registry.register_model("demo", str(path), {}, "", version="1")
    registry.set_active_version("demo", "1")
    svc.model_registry = registry
    module.preload_active_models(svc)

    token = jwt.encode(
        {"sub": "svc", "iss": "gateway", "exp": int(time.time()) + 60},
        "secret",
        algorithm="HS256",
    )
    assert verify_jwt_token(token)["iss"] == "gateway"
    headers = {"Authorization": f"Bearer {token}"}

    transport = httpx.ASGITransport(app=module.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/models/demo/predict",
            headers=headers,
            json={"data": [1, 2]},
        )
        assert resp.status_code == 200
        assert resp.json()["predictions"] == [2]
