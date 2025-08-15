#!/usr/bin/env python3
"""Generate OpenAPI JSON for FastAPI microservices."""
import importlib.util
import json
import os
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _stub_analytics_deps() -> None:
    """Stub heavy dependencies so the analytics app can be imported."""
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

    db_stub = types.ModuleType("services.common.async_db")
    db_stub.create_pool = lambda *a, **k: None
    db_stub.close_pool = lambda *a, **k: None
    db_stub.get_pool = lambda *a, **k: None
    sys.modules["services.common.async_db"] = db_stub

    config_stub = types.ModuleType("config")

    class _Cfg:
        def get_connection_string(self):
            return "postgresql://"

        initial_pool_size = 1
        max_pool_size = 1
        connection_timeout = 1

    class DatabaseSettings:
        def __init__(self):
            self.initial_pool_size = 1
            self.max_pool_size = 1
            self.connection_timeout = 1

        def get_connection_string(self) -> str:  # pragma: no cover - stub
            return "postgresql://"

    config_stub.get_database_config = lambda: _Cfg()
    dynamic_config_stub = types.ModuleType("config.dynamic_config")
    dynamic_config_stub.get_db_pool_size = lambda: 1
    dynamic_config_stub.get_db_connection_timeout = lambda: 1
    dynamic_config_stub.dynamic_config = types.SimpleNamespace(
        get_db_pool_size=lambda: 1,
        get_db_connection_timeout=lambda: 1,
    )
    config_stub.dynamic_config = dynamic_config_stub.dynamic_config
    config_stub.DatabaseSettings = DatabaseSettings
    sys.modules["config"] = config_stub
    sys.modules["config.dynamic_config"] = dynamic_config_stub

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
    import yosai_framework.service as yf_service

    yf_service.load_config = yf_config_stub.load_config

    redis_stub = types.ModuleType("redis")
    redis_async = types.ModuleType("redis.asyncio")
    redis_async.Redis = lambda *a, **k: None
    redis_stub.asyncio = redis_async
    sys.modules.setdefault("redis", redis_stub)
    sys.modules.setdefault("redis.asyncio", redis_async)

    queries_stub = types.ModuleType("services.analytics.async_queries")
    queries_stub.fetch_dashboard_summary = lambda *a, **k: {}
    queries_stub.fetch_access_patterns = lambda *a, **k: {}
    sys.modules["services.analytics.async_queries"] = queries_stub

    yd_models = types.ModuleType("yosai_intel_dashboard.models")
    ml_stub = types.ModuleType("yosai_intel_dashboard.models.ml")
    ml_stub.ModelRegistry = object
    yd_models.ml = ml_stub
    sys.modules.setdefault("yosai_intel_dashboard.models", yd_models)
    sys.modules.setdefault("yosai_intel_dashboard.models.ml", ml_stub)
    src_stub = types.ModuleType("yosai_intel_dashboard.src")
    infra_stub = types.ModuleType(
        "yosai_intel_dashboard.src.infrastructure.discovery.health_check"
    )
    infra_stub.health_check_router = None
    infra_stub.register_health_check = lambda app: None
    infra_stub.setup_health_checks = lambda app: None
    src_stub.infrastructure = types.SimpleNamespace(
        discovery=types.SimpleNamespace(health_check=infra_stub)
    )
    sys.modules.setdefault(
        "yosai_intel_dashboard.src.infrastructure.discovery.health_check", infra_stub
    )
    sys.modules.setdefault("yosai_intel_dashboard.src", src_stub)
    analytics_stub = types.ModuleType("analytics")
    analytics_stub.anomaly_detection = None
    analytics_stub.feature_extraction = None
    analytics_stub.security_patterns = None
    sys.modules.setdefault("analytics", analytics_stub)


def _stub_ingestion_deps() -> None:
    """Stub heavy dependencies for the ingestion service."""
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

    streaming_stub = types.ModuleType("services.streaming.service")

    class DummyStreamingService:
        def initialize(self):
            pass

        def consume(self, timeout=1.0):
            return []

        def close(self):
            pass

    streaming_stub.StreamingService = DummyStreamingService
    sys.modules["services.streaming.service"] = streaming_stub

    security_stub = types.ModuleType("services.security")
    security_stub.verify_service_jwt = lambda token: True
    sys.modules["services.security"] = security_stub

    tracing_stub = types.ModuleType("tracing")
    tracing_stub.trace_async_operation = lambda *a, **k: a[2] if len(a) > 2 else None
    tracing_stub.propagate_context = lambda headers: None
    sys.modules["tracing"] = tracing_stub


def load_app(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)  # type: ignore[arg-type]
        return module.app
    except Exception:
        from fastapi import FastAPI

        return FastAPI()


def main() -> None:
    if "JWT_SECRET" not in os.environ:
        try:
            from yosai_intel_dashboard.src.services.common.secrets import get_secret

            os.environ["JWT_SECRET"] = get_secret("secret/data/jwt#secret")
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(
                "JWT_SECRET must be supplied via environment variable or Vault"
            ) from exc

    os.environ.setdefault("LIGHTWEIGHT_SERVICES", "1")
    analytics_path = ROOT / "services" / "analytics_microservice" / "app.py"
    ingestion_path = ROOT / "services" / "event-ingestion" / "app.py"

    _stub_analytics_deps()
    _stub_ingestion_deps()

    analytics_app = load_app(analytics_path, "analytics_app")
    ingestion_app = load_app(ingestion_path, "ingestion_app")

    (ROOT / "docs" / "analytics_microservice_openapi.json").write_text(
        json.dumps(analytics_app.openapi(), indent=2)
    )
    (ROOT / "docs" / "event_ingestion_openapi.json").write_text(
        json.dumps(ingestion_app.openapi(), indent=2)
    )


if __name__ == "__main__":
    main()
