import importlib.util
import os
import pathlib
import sys
import types
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from jose import jwt

SERVICES_PATH = pathlib.Path(__file__).resolve().parents[2]

# Stub out the heavy 'services' package before tests import anything
services_stub = types.ModuleType("services")
services_stub.__path__ = [str(SERVICES_PATH)]
sys.modules.setdefault("services", services_stub)


@pytest.fixture
def module_stubs(monkeypatch):
    otel_stub = types.ModuleType("opentelemetry.instrumentation.fastapi")
    otel_stub.FastAPIInstrumentor = types.SimpleNamespace(
        instrument_app=lambda *a, **k: None
    )
    monkeypatch.setitem(
        sys.modules, "opentelemetry.instrumentation.fastapi", otel_stub
    )

    prom_stub = types.ModuleType("prometheus_fastapi_instrumentator")

    class DummyInstr:
        def instrument(self, app):
            return self

        def expose(self, app):
            return self

    prom_stub.Instrumentator = lambda: DummyInstr()
    monkeypatch.setitem(sys.modules, "prometheus_fastapi_instrumentator", prom_stub)

    import builtins

    monkeypatch.setattr(
        builtins, "ErrorHandlingMiddleware", lambda app, *a, **k: app, raising=False
    )
    monkeypatch.setattr(
        builtins, "rate_limit_decorator", lambda *a, **k: (lambda func: func), raising=False
    )

    db_stub = types.ModuleType("services.common.async_db")
    db_stub.create_pool = AsyncMock()
    db_stub.close_pool = AsyncMock()
    db_stub.get_pool = AsyncMock(return_value=object())
    monkeypatch.setitem(sys.modules, "services.common.async_db", db_stub)
    common_pkg = types.ModuleType("services.common")
    common_pkg.async_db = db_stub
    monkeypatch.setitem(sys.modules, "services.common", common_pkg)

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
    monkeypatch.setitem(sys.modules, "config.dynamic_config", dynamic_module)
    base_module = types.ModuleType("config.base")
    base_module.CacheConfig = lambda *a, **k: None
    monkeypatch.setitem(sys.modules, "config.base", base_module)
    db_exc_module = types.ModuleType("config.database_exceptions")

    class _UnicodeErr(Exception):
        pass

    db_exc_module.UnicodeEncodingError = _UnicodeErr
    monkeypatch.setitem(sys.modules, "config.database_exceptions", db_exc_module)
    monkeypatch.setitem(sys.modules, "config", config_stub)

    infra_config_stub = types.ModuleType(
        "yosai_intel_dashboard.src.infrastructure.config"
    )
    infra_config_stub.get_database_config = lambda: _Cfg()
    infra_loader_stub = types.ModuleType(
        "yosai_intel_dashboard.src.infrastructure.config.loader"
    )
    infra_loader_stub.ConfigurationLoader = lambda: types.SimpleNamespace(
        get_service_config=lambda: types.SimpleNamespace(redis_url="redis://")
    )
    monkeypatch.setitem(
        sys.modules, "yosai_intel_dashboard.src.infrastructure.config", infra_config_stub
    )
    monkeypatch.setitem(
        sys.modules,
        "yosai_intel_dashboard.src.infrastructure.config.loader",
        infra_loader_stub,
    )

    env_stub = types.ModuleType("config.environment")
    env_stub.get_environment = lambda: "test"
    monkeypatch.setitem(sys.modules, "config.environment", env_stub)

    validate_stub = types.ModuleType("config.validate")
    validate_stub.validate_required_env = lambda vars: None
    monkeypatch.setitem(sys.modules, "config.validate", validate_stub)

    pd_stub = types.ModuleType("pandas")

    def _read_csv(buf, *a, **k):
        text = buf.read().decode()
        lines = text.strip().splitlines()
        header = lines[0].split(",")
        return [dict(zip(header, line.split(","))) for line in lines[1:]]

    pd_stub.DataFrame = lambda data: data
    pd_stub.read_csv = _read_csv
    monkeypatch.setitem(sys.modules, "pandas", pd_stub)

    flask_stub = types.ModuleType("flask")
    flask_stub.Response = object
    flask_stub.jsonify = lambda *a, **k: None
    flask_stub.request = types.SimpleNamespace()
    flask_stub.url_for = lambda *a, **k: ""
    monkeypatch.setitem(sys.modules, "flask", flask_stub)

    prom_client_stub = types.ModuleType("prometheus_client")

    class DummyMetric:
        def labels(self, *a, **k):
            return self

        def inc(self, *a, **k):
            pass

        def set(self, *a, **k):
            pass

    prom_client_stub.REGISTRY = types.SimpleNamespace(_names_to_collectors={})
    prom_client_stub.Counter = lambda *a, **k: DummyMetric()
    prom_client_stub.Gauge = lambda *a, **k: DummyMetric()
    prom_client_stub.CollectorRegistry = lambda *a, **k: types.SimpleNamespace()
    monkeypatch.setitem(sys.modules, "prometheus_client", prom_client_stub)

    yaml_stub = types.ModuleType("yaml")
    yaml_stub.safe_load = lambda *a, **k: {}
    monkeypatch.setitem(sys.modules, "yaml", yaml_stub)

    jsonschema_stub = types.ModuleType("jsonschema")
    jsonschema_stub.validate = lambda *a, **k: None
    monkeypatch.setitem(sys.modules, "jsonschema", jsonschema_stub)

    sklearn_stub = types.ModuleType("sklearn")
    ensemble_stub = types.ModuleType("sklearn.ensemble")

    class IsolationForest:
        def __init__(self, *a, **k):
            pass

        def fit(self, *a, **k):
            pass

        def predict(self, *a, **k):
            return []

    ensemble_stub.IsolationForest = IsolationForest
    sklearn_stub.ensemble = ensemble_stub
    monkeypatch.setitem(sys.modules, "sklearn", sklearn_stub)
    monkeypatch.setitem(sys.modules, "sklearn.ensemble", ensemble_stub)

    yf_config_stub = types.ModuleType("yosai_framework.config")

    class DummyCfg:
        service_name = "analytics-test"
        log_level = "INFO"
        metrics_addr = ""
        tracing_endpoint = ""

    yf_config_stub.ServiceConfig = DummyCfg
    yf_config_stub.load_config = lambda path: DummyCfg()
    monkeypatch.setitem(sys.modules, "yosai_framework.config", yf_config_stub)

    redis_stub = types.ModuleType("redis")
    redis_async = types.ModuleType("redis.asyncio")
    redis_async.Redis = AsyncMock
    redis_stub.asyncio = redis_async
    monkeypatch.setitem(sys.modules, "redis", redis_stub)
    monkeypatch.setitem(sys.modules, "redis.asyncio", redis_async)

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
    monkeypatch.setitem(
        sys.modules, "services.analytics_microservice.analytics_service", analytics_stub
    )
    monkeypatch.setitem(
        sys.modules,
        "yosai_intel_dashboard.src.services.analytics_microservice.analytics_service",
        analytics_stub,
    )

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

    health_stub = types.ModuleType(
        "yosai_intel_dashboard.src.infrastructure.discovery.health_check"
    )
    health_stub.register_health_check = lambda *a, **k: None
    health_stub.setup_health_checks = lambda app: None
    health_stub.DependencyHealthMiddleware = lambda app: app
    monkeypatch.setitem(
        sys.modules,
        "yosai_intel_dashboard.src.infrastructure.discovery.health_check",
        health_stub,
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
            pass

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
    monkeypatch.setitem(sys.modules, "yosai_framework.service", service_stub)
    yf_pkg = types.ModuleType("yosai_framework")
    yf_pkg.ServiceBuilder = DummyBuilder
    yf_pkg.BaseService = DummyService
    monkeypatch.setitem(sys.modules, "yosai_framework", yf_pkg)
    errors_stub = types.ModuleType("yosai_framework.errors")

    class ServiceError(Exception):
        pass

    errors_stub.ServiceError = ServiceError
    errors_stub.CODE_TO_STATUS = {}
    monkeypatch.setitem(sys.modules, "yosai_framework.errors", errors_stub)

    secrets_stub = types.ModuleType("services.common.secrets")
    secrets_stub.get_secret = lambda path: "secret"
    monkeypatch.setitem(sys.modules, "services.common.secrets", secrets_stub)

    auth_stub = types.ModuleType("services.auth")
    auth_stub.verify_jwt_token = lambda token: jwt.decode(
        token, os.environ["JWT_SECRET_KEY"], algorithms=["HS256"]
    )
    monkeypatch.setitem(sys.modules, "services.auth", auth_stub)
    monkeypatch.setitem(
        sys.modules, "yosai_intel_dashboard.src.services.auth", auth_stub
    )

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
    monkeypatch.setitem(sys.modules, "models.ml.model_registry", registry_mod)
    monkeypatch.setitem(
        sys.modules, "yosai_intel_dashboard.models.ml.model_registry", registry_mod
    )
    ml_pkg = types.ModuleType("models.ml")
    ml_pkg.ModelRegistry = DummyRegistry
    ml_pkg.ModelRecord = DummyRecord
    monkeypatch.setitem(sys.modules, "models.ml", ml_pkg)
    monkeypatch.setitem(sys.modules, "yosai_intel_dashboard.models.ml", ml_pkg)
    models_stub = types.ModuleType("models")
    models_stub.ml = ml_pkg
    monkeypatch.setitem(sys.modules, "models", models_stub)
    monkeypatch.setitem(sys.modules, "yosai_intel_dashboard.models", models_stub)

    fe_stub = types.ModuleType("analytics.feature_extraction")
    fe_stub.extract_event_features = lambda df, logger=None: df

    ad_stub = types.ModuleType("analytics.anomaly_detection")

    @dataclass
    class DummyResult:
        total_anomalies: int = 0
        severity_distribution: dict | None = None
        detection_summary: dict | None = None
        risk_assessment: dict | None = None
        recommendations: list | None = None
        processing_metadata: dict | None = None

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
        threat_indicators: list | None = None
        pattern_analysis: dict | None = None
        recommendations: list | None = None

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
    monkeypatch.setitem(sys.modules, "analytics", analytics_pkg)
    monkeypatch.setitem(sys.modules, "analytics.feature_extraction", fe_stub)
    monkeypatch.setitem(sys.modules, "analytics.anomaly_detection", ad_stub)
    monkeypatch.setitem(sys.modules, "analytics.security_patterns", sp_stub)

    pipeline_stub = types.ModuleType(
        "yosai_intel_dashboard.models.ml.pipeline_contract"
    )
    pipeline_stub.preprocess_events = lambda df: df
    ml_pkg.pipeline_contract = pipeline_stub
    monkeypatch.setitem(
        sys.modules,
        "yosai_intel_dashboard.models.ml.pipeline_contract",
        pipeline_stub,
    )
    monkeypatch.setitem(sys.modules, "models.ml.pipeline_contract", pipeline_stub)

    core_unicode = types.ModuleType("core.unicode")
    core_unicode.sanitize_for_utf8 = lambda x: x
    core_pkg = types.ModuleType("core")
    core_pkg.unicode = core_unicode
    security_stub = types.ModuleType("core.security")

    class DummyRateLimiter:
        async def is_allowed(self, *a, **k):
            return {"allowed": True}

    security_stub.RateLimiter = DummyRateLimiter
    security_stub.security_config = types.SimpleNamespace(
        get_secret=lambda *a, **k: os.environ.get("JWT_SECRET_KEY", "secret")
    )
    core_pkg.security = security_stub
    monkeypatch.setitem(sys.modules, "core", core_pkg)
    monkeypatch.setitem(sys.modules, "core.unicode", core_unicode)
    monkeypatch.setitem(sys.modules, "core.security", security_stub)
    monkeypatch.setitem(
        sys.modules, "yosai_intel_dashboard.src.core.security", security_stub
    )

    unicode_stub = types.ModuleType("utils.unicode_handler")

    class DummyHandler:
        @staticmethod
        def sanitize(obj):
            return obj

    unicode_stub.UnicodeHandler = DummyHandler
    monkeypatch.setitem(sys.modules, "utils.unicode_handler", unicode_stub)

    val_stub = types.ModuleType("validation.unicode_validator")

    class DummyValidator:
        def validate_dataframe(self, df):
            return df

    val_stub.UnicodeValidator = DummyValidator
    monkeypatch.setitem(sys.modules, "validation.unicode_validator", val_stub)

    monkeypatch.setitem(sys.modules, "tracing", types.ModuleType("tracing"))
    monkeypatch.setitem(sys.modules, "hvac", types.ModuleType("hvac"))

    return queries_stub, dummy_service


@pytest.fixture
def jwt_secret_env(monkeypatch):
    def setter(secret: str | None = "secret"):
        if secret is not None:
            monkeypatch.setenv("JWT_SECRET_KEY", secret)
        else:
            monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
        monkeypatch.setenv("SECRET_KEY", "dummy")
        return secret

    return setter


@pytest.fixture
def app_factory(module_stubs, jwt_secret_env):
    queries_stub, dummy_service = module_stubs

    def factory(secret: str | None = "secret"):
        jwt_secret_env(secret)
        spec = importlib.util.spec_from_file_location(
            "services.analytics_microservice.app",
            SERVICES_PATH / "analytics_microservice" / "app.py",
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore[arg-type]
        module.app.state.ready = True
        module.app.state.startup_complete = True
        module.app.state.analytics_service = dummy_service
        return module, queries_stub, dummy_service

    return factory
