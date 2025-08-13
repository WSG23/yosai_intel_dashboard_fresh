import importlib.util
import os
import pathlib
import sys
import types
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi import FastAPI
from jose import jwt
import time

SERVICES_PATH = pathlib.Path(__file__).resolve().parents[2]

# Stub out the heavy 'services' package before tests import anything
services_stub = types.ModuleType("services")
services_stub.__path__ = [str(SERVICES_PATH)]
sys.modules.setdefault("services", services_stub)

# Stub hierarchical packages to prevent loading the full application
yosai_stub = types.ModuleType("yosai_intel_dashboard")
yosai_stub.__path__ = [str(SERVICES_PATH.parent)]
src_stub = types.ModuleType("yosai_intel_dashboard.src")
src_stub.__path__ = [str(SERVICES_PATH.parent)]
services_pkg_stub = types.ModuleType("yosai_intel_dashboard.src.services")
services_pkg_stub.__path__ = [str(SERVICES_PATH)]
sys.modules.setdefault("yosai_intel_dashboard", yosai_stub)
sys.modules.setdefault("yosai_intel_dashboard.src", src_stub)
sys.modules.setdefault("yosai_intel_dashboard.src.services", services_pkg_stub)


def _register_environment_stubs(monkeypatch: pytest.MonkeyPatch) -> None:
    """Stub external modules that the analytics microservice depends on."""
    import builtins

    otel = types.SimpleNamespace(
        FastAPIInstrumentor=types.SimpleNamespace(instrument_app=lambda *a, **k: None)
    )
    prom = types.SimpleNamespace(
        Instrumentator=lambda: types.SimpleNamespace(
            instrument=lambda app: None, expose=lambda app: None
        )
    )
    monkeypatch.setitem(sys.modules, "opentelemetry.instrumentation.fastapi", otel)
    monkeypatch.setitem(sys.modules, "prometheus_fastapi_instrumentator", prom)
    monkeypatch.setattr(
        builtins, "ErrorHandlingMiddleware", lambda app, *a, **k: app, raising=False
    )
    monkeypatch.setattr(
        builtins, "rate_limit_decorator", lambda *a, **k: (lambda f: f), raising=False
    )

    db = types.SimpleNamespace(
        create_pool=AsyncMock(),
        close_pool=AsyncMock(),
        get_pool=AsyncMock(return_value=object()),
    )
    monkeypatch.setitem(sys.modules, "services.common.async_db", db)
    cfg = types.SimpleNamespace(
        type="sqlite",
        host="localhost",
        port=5432,
        name="test",
        user="user",
        password="",
        connection_timeout=1,
        get_connection_string=lambda: "postgresql://",
        initial_pool_size=1,
        max_pool_size=1,
    )
    monkeypatch.setitem(
        sys.modules,
        "config",
        types.SimpleNamespace(DatabaseSettings=lambda: cfg, get_database_config=lambda: cfg),
    )
    monkeypatch.setitem(
        sys.modules,
        "yosai_intel_dashboard.src.infrastructure.config",
        types.SimpleNamespace(get_database_config=lambda: cfg),
    )
    loader_stub = types.SimpleNamespace(
        ConfigurationLoader=lambda: types.SimpleNamespace(
            get_service_config=lambda: types.SimpleNamespace(redis_url="redis://test")
        )
    )
    monkeypatch.setitem(
        sys.modules,
        "yosai_intel_dashboard.src.infrastructure.config.loader",
        loader_stub,
    )
    monkeypatch.setitem(
        sys.modules,
        "yosai_intel_dashboard.src.database.utils",
        types.SimpleNamespace(parse_connection_string=lambda *a, **k: None),
    )
    monkeypatch.setitem(sys.modules, "config.dynamic_config", types.SimpleNamespace(dynamic_config={}))
    monkeypatch.setitem(sys.modules, "config.base", types.SimpleNamespace(CacheConfig=lambda *a, **k: None))
    monkeypatch.setitem(
        sys.modules, "config.database_exceptions", types.SimpleNamespace(UnicodeEncodingError=Exception)
    )
    monkeypatch.setitem(
        sys.modules, "config.environment", types.SimpleNamespace(get_environment=lambda: "test")
    )
    monkeypatch.setitem(
        sys.modules, "config.validate", types.SimpleNamespace(validate_required_env=lambda vars: None)
    )

    class DummyCfg:
        service_name = "analytics-test"
        log_level = "INFO"
        metrics_addr = ""
        tracing_endpoint = ""

    monkeypatch.setitem(
        sys.modules,
        "yosai_framework.config",
        types.SimpleNamespace(ServiceConfig=DummyCfg, load_config=lambda path: DummyCfg()),
    )

    redis_async = types.SimpleNamespace(Redis=AsyncMock)
    monkeypatch.setitem(sys.modules, "redis.asyncio", redis_async)
    monkeypatch.setitem(sys.modules, "redis", types.SimpleNamespace(asyncio=redis_async))

    hc = types.SimpleNamespace(
        register_health_check=lambda *a, **k: None,
        setup_health_checks=lambda app: None,
        DependencyHealthMiddleware=lambda app: app,
    )
    monkeypatch.setitem(
        sys.modules,
        "yosai_intel_dashboard.src.infrastructure.discovery.health_check",
        hc,
    )

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
            self.name = name

        def with_logging(self, *a, **k):
            return self

        def with_metrics(self, *a, **k):
            return self

        def with_health(self):
            return self

        def build(self):
            return DummyService()

    monkeypatch.setitem(
        sys.modules,
        "yosai_framework.service",
        types.SimpleNamespace(BaseService=DummyService, ServiceBuilder=DummyBuilder),
    )
    monkeypatch.setitem(
        sys.modules,
        "yosai_framework",
        types.SimpleNamespace(ServiceBuilder=DummyBuilder, BaseService=DummyService),
    )
    monkeypatch.setitem(
        sys.modules, "yosai_framework.errors", types.SimpleNamespace(ServiceError=Exception)
    )

    class DummyRateLimiter:
        async def is_allowed(self, *a, **k):
            return {"allowed": True}

    security_config = types.SimpleNamespace(
        get_secret=lambda key, vault_key=None: os.environ.get(key, "")
    )
    sec_mod = types.SimpleNamespace(
        RateLimiter=DummyRateLimiter, security_config=security_config
    )
    unicode_mod = types.SimpleNamespace(sanitize_for_utf8=lambda x: x)
    handler_mod = types.SimpleNamespace(
        UnicodeHandler=types.SimpleNamespace(sanitize=lambda obj: obj)
    )
    validator_mod = types.SimpleNamespace(
        UnicodeValidator=lambda: types.SimpleNamespace(validate_dataframe=lambda df: df)
    )
    monkeypatch.setitem(sys.modules, "core.security", sec_mod)
    monkeypatch.setitem(sys.modules, "core.unicode", unicode_mod)
    monkeypatch.setitem(sys.modules, "utils.unicode_handler", handler_mod)
    monkeypatch.setitem(sys.modules, "validation.unicode_validator", validator_mod)
    # mirrored paths used by application modules
    monkeypatch.setitem(sys.modules, "yosai_intel_dashboard.src.core.security", sec_mod)
    monkeypatch.setitem(sys.modules, "yosai_intel_dashboard.src.core.unicode", unicode_mod)
    monkeypatch.setitem(
        sys.modules, "yosai_intel_dashboard.src.utils.unicode_handler", handler_mod
    )
    monkeypatch.setitem(
        sys.modules, "yosai_intel_dashboard.src.validation.unicode_validator", validator_mod
    )
    monkeypatch.setitem(sys.modules, "tracing", types.ModuleType("tracing"))
    monkeypatch.setitem(sys.modules, "hvac", types.ModuleType("hvac"))

    monkeypatch.setitem(
        sys.modules,
        "services.common.secrets",
        types.SimpleNamespace(get_secret=lambda path: "secret"),
    )

    auth = types.SimpleNamespace(
        verify_jwt_token=lambda token: jwt.decode(
            token, os.environ["JWT_SECRET_KEY"], algorithms=["HS256"]
        )
    )
    monkeypatch.setitem(sys.modules, "services.auth", auth)

    def _read_csv(buffer):
        import csv, io

        text = buffer.read().decode()
        reader = csv.reader(io.StringIO(text))
        headers = next(reader, None)
        return [list(map(int, row)) for row in reader]

    pandas_stub = types.SimpleNamespace(DataFrame=lambda data: data, read_csv=_read_csv)
    monkeypatch.setitem(sys.modules, "pandas", pandas_stub)

    # Simple in-memory model registry used by the microservice
    @dataclass
    class DummyRecord:
        name: str
        version: str
        storage_uri: str
        is_active: bool = False

    class DummyRegistry:
        def __init__(self):
            self.models: dict[str, dict[str, DummyRecord]] = {}

        def register_model(
            self,
            name: str,
            model_path: str,
            metrics: dict,
            dataset_hash: str,
            *,
            version: str | None = None,
            training_date: object | None = None,
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
            res: list[DummyRecord] = []
            for d in self.models.values():
                res.extend(d.values())
            return res

        def download_artifact(self, src: str, dest: str) -> None:
            Path(dest).write_bytes(Path(src).read_bytes())

    registry_mod = types.ModuleType("models.ml.model_registry")
    registry_mod.ModelRegistry = DummyRegistry
    registry_mod.ModelRecord = DummyRecord
    ml_module = types.ModuleType("yosai_intel_dashboard.models.ml")
    ml_module.ModelRegistry = DummyRegistry
    ml_module.ModelRecord = DummyRecord
    monkeypatch.setitem(sys.modules, "yosai_intel_dashboard.models.ml", ml_module)
    monkeypatch.setitem(sys.modules, "models.ml", ml_module)
    registry_mod = types.ModuleType("models.ml.model_registry")
    registry_mod.ModelRegistry = DummyRegistry
    registry_mod.ModelRecord = DummyRecord
    monkeypatch.setitem(sys.modules, "models.ml.model_registry", registry_mod)
    monkeypatch.setitem(
        sys.modules, "yosai_intel_dashboard.models.ml.model_registry", registry_mod
    )
    models_pkg = types.ModuleType("models")
    models_pkg.ml = ml_module
    models_pkg.__path__ = []
    yd_models_pkg = types.ModuleType("yosai_intel_dashboard.models")
    yd_models_pkg.ml = ml_module
    yd_models_pkg.__path__ = []
    monkeypatch.setitem(sys.modules, "models", models_pkg)
    monkeypatch.setitem(sys.modules, "yosai_intel_dashboard.models", yd_models_pkg)

    # Minimal analytics and pipeline modules used during model loading
    analytics_pkg = types.ModuleType("analytics")
    analytics_pkg.feature_extraction = types.SimpleNamespace(
        extract_event_features=lambda df, logger=None: df
    )
    analytics_pkg.anomaly_detection = types.SimpleNamespace(
        AnomalyDetector=lambda: types.SimpleNamespace(
            analyze_anomalies=lambda df: types.SimpleNamespace(
                severity_distribution={},
                detection_summary={},
                risk_assessment={"risk_score": 0},
                recommendations=[],
                processing_metadata={},
            )
        )
    )
    analytics_pkg.security_patterns = types.SimpleNamespace(
        SecurityPatternsAnalyzer=lambda: types.SimpleNamespace(
            analyze_security_patterns=lambda df: types.SimpleNamespace(
                overall_score=0,
                risk_level="low",
                confidence_interval=(0.0, 0.0),
                threat_indicators=[],
                pattern_analysis={},
                recommendations=[],
            )
        )
    )
    monkeypatch.setitem(sys.modules, "analytics", analytics_pkg)
    for name in ["feature_extraction", "anomaly_detection", "security_patterns"]:
        monkeypatch.setitem(sys.modules, f"analytics.{name}", getattr(analytics_pkg, name))

    pipeline_stub = types.ModuleType(
        "yosai_intel_dashboard.models.ml.pipeline_contract"
    )
    pipeline_stub.preprocess_events = lambda df: df
    monkeypatch.setitem(
        sys.modules, "yosai_intel_dashboard.models.ml.pipeline_contract", pipeline_stub
    )

    # Error handling modules without Flask dependency
    from fastapi import HTTPException

    error_mod = types.ModuleType("yosai_intel_dashboard.src.error_handling")
    error_mod.http_error = lambda code, message, status_code: HTTPException(
        status_code, {"code": code, "message": message}
    )
    monkeypatch.setitem(
        sys.modules, "yosai_intel_dashboard.src.error_handling", error_mod
    )
    middleware_mod = types.ModuleType(
        "yosai_intel_dashboard.src.error_handling.middleware"
    )
    middleware_mod.ErrorHandlingMiddleware = lambda app, *a, **k: app
    monkeypatch.setitem(
        sys.modules,
        "yosai_intel_dashboard.src.error_handling.middleware",
        middleware_mod,
    )


@pytest.fixture(autouse=True)
def env_setup(monkeypatch):
    _register_environment_stubs(monkeypatch)


@pytest.fixture
def mock_services(monkeypatch):
    queries_stub = types.ModuleType("services.analytics_microservice.async_queries")
    queries_stub.fetch_dashboard_summary = AsyncMock(return_value={"status": "ok"})
    queries_stub.fetch_access_patterns = AsyncMock(return_value={"days": 7})
    monkeypatch.setitem(
        sys.modules, "services.analytics_microservice.async_queries", queries_stub
    )
    monkeypatch.setitem(
        sys.modules,
        "yosai_intel_dashboard.src.services.analytics_microservice.async_queries",
        queries_stub,
    )

    class DummyAnalyticsService:
        def __init__(self, *a, **k):
            self.redis = types.SimpleNamespace(get=AsyncMock(), set=AsyncMock())
            self.pool = object()
            self.model_registry = None
            self.cache_ttl = 300
            self.model_dir = Path("/tmp")
            self.models = {}

        async def close(self):
            pass

    dummy_service = DummyAnalyticsService()
    analytics_stub = types.ModuleType(
        "services.analytics_microservice.analytics_service"
    )
    analytics_stub.AnalyticsService = DummyAnalyticsService
    analytics_stub.get_analytics_service = lambda *a, **k: dummy_service
    monkeypatch.setitem(
        sys.modules, "services.analytics_microservice.analytics_service", analytics_stub
    )
    monkeypatch.setitem(
        sys.modules,
        "yosai_intel_dashboard.src.services.analytics_microservice.analytics_service",
        analytics_stub,
    )

    return queries_stub, dummy_service


def _load_app(dummy_service, secret: str | None):
    if secret is not None:
        os.environ["JWT_SECRET_KEY"] = secret
    else:
        os.environ.pop("JWT_SECRET_KEY", None)

    spec = importlib.util.spec_from_file_location(
        "services.analytics_microservice.app",
        SERVICES_PATH / "analytics_microservice" / "app.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[arg-type]

    module.app.state.ready = True
    module.app.state.startup_complete = True
    module.app.state.analytics_service = dummy_service
    return module


@pytest.fixture
def app_factory(mock_services):
    queries_stub, dummy_service = mock_services

    def factory(secret: str | None = "secret"):
        module = _load_app(dummy_service, secret)
        return module, queries_stub, dummy_service

    return factory


@pytest.fixture
def token_factory():
    from yosai_intel_dashboard.src.services.auth import verify_jwt_token

    def factory(**claims):
        payload = {
            "sub": "svc",
            "iss": "gateway",
            "exp": int(time.time()) + 60,
        }
        payload.update(claims)
        token = jwt.encode(payload, "secret", algorithm="HS256")
        assert verify_jwt_token(token)["iss"] == payload["iss"]
        return token

    return factory


@pytest.fixture
def client():
    def factory(app):
        transport = httpx.ASGITransport(app=app)
        return httpx.AsyncClient(transport=transport, base_url="http://test")

    return factory
