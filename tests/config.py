"""Central test configuration utilities.

Importing this module initialises the test environment by:
- setting required environment variables
- ensuring the project root is importable
- registering lightweight stubs for optional third‑party packages

It also exposes a couple of small fixtures used across the suite.
"""

from __future__ import annotations

import importlib
import importlib.abc
import importlib.machinery
import importlib.util
import os
import sys
import types
from pathlib import Path

import pytest

from optional_dependencies import register_fallback

PROJECT_ROOT = Path(__file__).resolve().parents[1]

SECRET_KEY = os.getenv("TEST_SECRET_KEY", "dynamically-generated-test-key")
API_TOKEN = os.getenv("TEST_API_TOKEN", "dynamically-generated-test-token")


def set_test_environment() -> None:
    """Populate minimal environment variables for tests."""
    os.environ.setdefault("YOSAI_ENV", "testing")
    os.environ.setdefault("FLASK_ENV", "testing")
    os.environ.setdefault("SECRET_KEY", SECRET_KEY)
    os.environ.setdefault("API_TOKEN", API_TOKEN)

    # enable lightweight implementations for optional services
    os.environ.setdefault("LIGHTWEIGHT_SERVICES", "1")


def add_project_root_to_sys_path() -> None:
    """Ensure the repository root is importable."""
    root_str = str(PROJECT_ROOT)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)


def register_dependency_stubs() -> None:
    """Register lightweight stubs for optional dependencies."""

    def _simple_module(name: str, **attrs: object) -> types.ModuleType:
        mod = types.ModuleType(name)
        for key, value in attrs.items():
            setattr(mod, key, value)
        return mod

    register_fallback("hvac", _simple_module("hvac", Client=object))
    sys.modules.setdefault("hvac", _simple_module("hvac", Client=object))

    class _DummyFernet:
        def __init__(self, *a, **k): ...

        @staticmethod
        def generate_key() -> bytes:
            return b""

        def encrypt(self, data: bytes) -> bytes:
            return data

        def decrypt(self, data: bytes) -> bytes:
            return data

    register_fallback(
        "cryptography.fernet",
        _simple_module("cryptography.fernet", Fernet=_DummyFernet),
    )
    sys.modules.setdefault(
        "cryptography.fernet",
        _simple_module("cryptography.fernet", Fernet=_DummyFernet),
    )

    register_fallback("boto3", _simple_module("boto3", client=lambda *a, **k: object()))
    sys.modules.setdefault(
        "boto3", _simple_module("boto3", client=lambda *a, **k: object())
    )

    class _DummyRun:
        def __init__(self) -> None:
            self.info = types.SimpleNamespace(run_id="run")

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

    register_fallback(
        "mlflow",
        _simple_module(
            "mlflow",
            start_run=lambda *a, **k: _DummyRun(),
            log_metric=lambda *a, **k: None,
            log_artifact=lambda *a, **k: None,
            log_text=lambda *a, **k: None,
            set_tracking_uri=lambda *a, **k: None,
        ),
    )
    sys.modules.setdefault(
        "mlflow",
        _simple_module(
            "mlflow",
            start_run=lambda *a, **k: _DummyRun(),
            log_metric=lambda *a, **k: None,
            log_artifact=lambda *a, **k: None,
            log_text=lambda *a, **k: None,
            set_tracking_uri=lambda *a, **k: None,
        ),
    )

    register_fallback(
        "asyncpg", _simple_module("asyncpg", create_pool=lambda *a, **k: None)
    )
    sys.modules.setdefault(
        "asyncpg", _simple_module("asyncpg", create_pool=lambda *a, **k: None)
    )
    try:
        import httpx  # noqa: F401
    except Exception:  # pragma: no cover - fallback when httpx unavailable
        register_fallback(
            "httpx",
            _simple_module(
                "httpx", ASGITransport=object, AsyncClient=object, Response=object
            ),
        )
        sys.modules.setdefault(
            "httpx",
            _simple_module(
                "httpx", ASGITransport=object, AsyncClient=object, Response=object
            ),
        )
    register_fallback("structlog", _simple_module("structlog", BoundLogger=object))
    sys.modules.setdefault("structlog", _simple_module("structlog", BoundLogger=object))
    register_fallback("confluent_kafka", _simple_module("confluent_kafka"))
    sys.modules.setdefault("confluent_kafka", _simple_module("confluent_kafka"))

    _dash = _simple_module("dash", Dash=object)
    _dash.html = _simple_module("dash.html")
    _dash.dcc = _simple_module("dash.dcc")
    _dash.dependencies = _simple_module(
        "dash.dependencies", Input=object, Output=object, State=object
    )
    _dash._callback = _simple_module("dash._callback")
    register_fallback("dash", _dash)
    register_fallback("dash.html", _dash.html)
    register_fallback("dash.dcc", _dash.dcc)
    register_fallback("dash.dependencies", _dash.dependencies)
    register_fallback("dash._callback", _dash._callback)
    register_fallback(
        "dash_bootstrap_components", _simple_module("dash_bootstrap_components")
    )
    sys.modules.setdefault("dash", _dash)
    sys.modules.setdefault("dash.html", _dash.html)
    sys.modules.setdefault("dash.dcc", _dash.dcc)
    sys.modules.setdefault("dash.dependencies", _dash.dependencies)
    sys.modules.setdefault("dash._callback", _dash._callback)
    sys.modules.setdefault(
        "dash_bootstrap_components", _simple_module("dash_bootstrap_components")
    )

    class _DummyRedis:
        @classmethod
        def from_url(cls, url):
            return cls()

        def pipeline(self):
            return self

        def incr(self, *a, **k):
            pass

        def expire(self, *a, **k):
            pass

        def execute(self):
            return (0, None)

        def ttl(self, key):
            return 0

    _redis = _simple_module("redis", Redis=_DummyRedis)
    _redis.asyncio = _simple_module("redis.asyncio")
    register_fallback("redis", _redis)
    register_fallback("redis.asyncio", _redis.asyncio)
    register_fallback("requests", _simple_module("requests"))
    sys.modules.setdefault("redis", _redis)
    sys.modules.setdefault("redis.asyncio", _redis.asyncio)
    sys.modules.setdefault("requests", _simple_module("requests"))

    # Minimal stubs for protobuf dependencies used during configuration import
    google_pkg = _simple_module("google")
    google_pkg.__path__ = []
    symbol_db = _simple_module(
        "google.protobuf.symbol_database",
        Default=lambda: types.SimpleNamespace(RegisterMessage=lambda *a, **k: None),
    )
    descriptor_pool = _simple_module(
        "google.protobuf.descriptor_pool",
        Default=lambda: types.SimpleNamespace(
            AddSerializedFile=lambda *a, **k: types.SimpleNamespace()
        ),
    )
    descriptor = _simple_module("google.protobuf.descriptor", _USE_C_DESCRIPTORS=False)
    builder = _simple_module(
        "google.protobuf.internal.builder",
        BuildMessageAndEnumDescriptors=lambda *a, **k: None,
        BuildTopDescriptorsAndMessages=lambda *a, **k: None,
    )
    internal_pkg = _simple_module("google.protobuf.internal", builder=builder)
    internal_pkg.__path__ = []
    protobuf_pkg = _simple_module(
        "google.protobuf",
        symbol_database=symbol_db,
        descriptor_pool=descriptor_pool,
        descriptor=descriptor,
        internal=internal_pkg,
    )
    protobuf_pkg.__path__ = []
    register_fallback("google", google_pkg)
    register_fallback("google.protobuf", protobuf_pkg)
    register_fallback("google.protobuf.symbol_database", symbol_db)
    register_fallback("google.protobuf.descriptor_pool", descriptor_pool)
    register_fallback("google.protobuf.descriptor", descriptor)
    register_fallback("google.protobuf.internal", internal_pkg)
    register_fallback("google.protobuf.internal.builder", builder)
    sys.modules.setdefault("google", google_pkg)
    sys.modules.setdefault("google.protobuf", protobuf_pkg)
    sys.modules.setdefault("google.protobuf.symbol_database", symbol_db)
    sys.modules.setdefault("google.protobuf.descriptor_pool", descriptor_pool)
    sys.modules.setdefault("google.protobuf.descriptor", descriptor)
    sys.modules.setdefault("google.protobuf.internal", internal_pkg)
    sys.modules.setdefault("google.protobuf.internal.builder", builder)

    # Lightweight stubs for database and query optimizer dependencies
    database_pkg = _simple_module("database")
    database_pkg.__path__ = []
    connection_stub = _simple_module(
        "database.connection", create_database_connection=lambda *a, **k: object()
    )
    secure_exec_stub = _simple_module(
        "database.secure_exec",
        execute_query=lambda *a, **k: [],
        execute_command=lambda *a, **k: None,
    )
    query_builder_stub = _simple_module(
        "infrastructure.security.query_builder",
        SecureQueryBuilder=lambda *a, **k: types.SimpleNamespace(
            table=lambda x: x, column=lambda x: x, build=lambda q, logger=None: (q, [])
        ),
    )
    register_fallback("database", database_pkg)
    register_fallback("database.connection", connection_stub)
    register_fallback("database.secure_exec", secure_exec_stub)
    register_fallback("infrastructure.security.query_builder", query_builder_stub)
    sys.modules.setdefault("database", database_pkg)
    sys.modules.setdefault("database.connection", connection_stub)
    sys.modules.setdefault("database.secure_exec", secure_exec_stub)
    sys.modules.setdefault("infrastructure.security.query_builder", query_builder_stub)

    config_manager_stub = _simple_module(
        "yosai_intel_dashboard.src.infrastructure.config.config_manager",
        ConfigManager=type(
            "ConfigManager", (), {"__init__": lambda self, *a, **k: None}
        ),
        get_config=lambda: types.SimpleNamespace(),
        reload_config=lambda: None,
    )
    register_fallback(
        "yosai_intel_dashboard.src.infrastructure.config.config_manager",
        config_manager_stub,
    )
    sys.modules.setdefault(
        "yosai_intel_dashboard.src.infrastructure.config.config_manager",
        config_manager_stub,
    )

    config_pb2_path = (
        "yosai_intel_dashboard.src.infrastructure.config.generated.protobuf.config."
        "schema.config_pb2"
    )
    config_pb2_stub = _simple_module(
        config_pb2_path, YosaiConfig=type("YosaiConfig", (), {})
    )
    register_fallback(config_pb2_path, config_pb2_stub)
    sys.modules.setdefault(config_pb2_path, config_pb2_stub)

    # Common scientific and monitoring libraries can be heavy optional
    # dependencies.  Provide lightweight stand-ins so modules importing
    # them at module level do not fail during test collection.  The stubs
    # only expose the minimal attributes used in tests.

    numpy_stub = _simple_module("numpy", asarray=lambda x, dtype=None: x)
    register_fallback("numpy", numpy_stub)
    sys.modules.setdefault("numpy", numpy_stub)

    pandas_stub = _simple_module("pandas", DataFrame=object)
    register_fallback("pandas", pandas_stub)
    sys.modules.setdefault("pandas", pandas_stub)

    psutil_stub = _simple_module("psutil")
    psutil_stub.__spec__ = importlib.machinery.ModuleSpec("psutil", loader=None)
    register_fallback("psutil", psutil_stub)
    sys.modules.setdefault("psutil", psutil_stub)

    class _SafeLoader:
        @classmethod
        def add_constructor(cls, *a, **k):
            pass

        def __init__(self, *a, **k):
            self._root = None

        def get_single_data(self):
            return {}

        def dispose(self):
            pass

    yaml_stub = _simple_module(
        "yaml", SafeLoader=_SafeLoader, Node=object, safe_load=lambda *a, **k: {}
    )
    yaml_stub.__spec__ = importlib.machinery.ModuleSpec("yaml", loader=None)
    register_fallback("yaml", yaml_stub)
    sys.modules.setdefault("yaml", yaml_stub)

    class _Counter:
        def __init__(self, *a, **k):
            self._value = type("V", (), {"get": lambda self: 0})()

        def inc(self, *a, **k):
            pass

    class _CollectorRegistry:
        pass

    prom_core = _simple_module(
        "prometheus_client.core", CollectorRegistry=_CollectorRegistry
    )
    prom_client = _simple_module(
        "prometheus_client",
        REGISTRY=types.SimpleNamespace(_names_to_collectors={}),
        Counter=_Counter,
        Gauge=_Counter,
        Histogram=_Counter,
        CollectorRegistry=_CollectorRegistry,
        core=prom_core,
    )
    register_fallback("prometheus_client", prom_client)
    register_fallback("prometheus_client.core", prom_core)
    sys.modules.setdefault("prometheus_client", prom_client)
    sys.modules.setdefault("prometheus_client.core", prom_core)

    pydantic_stub = _simple_module("pydantic")

    class _BaseModel:
        pass

    def _validator(*a, **k):
        def _wrap(fn):
            return fn

        return _wrap

    pydantic_stub.BaseModel = _BaseModel
    pydantic_stub.Field = lambda *a, **k: None
    pydantic_stub.ValidationError = Exception
    pydantic_stub.validator = _validator
    pydantic_stub.model_validator = _validator
    register_fallback("pydantic", pydantic_stub)
    sys.modules.setdefault("pydantic", pydantic_stub)

    core_pkg = _simple_module("yosai_intel_dashboard.src.core")
    core_pkg.__path__ = []
    sys.modules.setdefault("yosai_intel_dashboard.src.core", core_pkg)

    # Minimal stubs for optional security integrations
    # Only register when the real package is unavailable
    if importlib.util.find_spec("yosai_intel_dashboard.src.core.integrations") is None:
        core_integrations_stub = _simple_module("core.integrations")
        core_integrations_stub.__path__ = []
        register_fallback("core.integrations", core_integrations_stub)
        sys.modules.setdefault("core.integrations", core_integrations_stub)
        siem_stub = _simple_module(
            "core.integrations.siem_connectors", send_to_siem=lambda *a, **k: None
        )
        register_fallback("core.integrations.siem_connectors", siem_stub)
        sys.modules.setdefault("core.integrations.siem_connectors", siem_stub)

    # As a final fallback, provide a meta-path finder that returns empty
    # modules for any remaining missing imports.  Each stubbed module
    # lazily creates placeholders for arbitrary attributes so ``from pkg
    # import name`` succeeds without the real dependency installed.

    class _LazyModule(types.ModuleType):
        def __init__(self, name: str) -> None:
            super().__init__(name)
            # Mark as a package so submodules can be imported without errors
            self.__path__ = []  # type: ignore[attr-defined]

        def __getattr__(self, name: str) -> types.ModuleType:
            mod = _simple_module(f"{self.__name__}.{name}")
            setattr(self, name, mod)
            return mod

    class _MissingModuleFinder(importlib.abc.MetaPathFinder, importlib.abc.Loader):
        def find_spec(self, fullname, path, target=None):  # type: ignore[override]
            if fullname in sys.modules:
                return None
            return importlib.machinery.ModuleSpec(fullname, self)

        def create_module(self, spec):  # type: ignore[override]
            return _LazyModule(spec.name)

        def exec_module(self, module):  # type: ignore[override]
            module.__spec__ = importlib.machinery.ModuleSpec(module.__name__, self)

    sys.meta_path.append(_MissingModuleFinder())

    config_pkg = _simple_module("yosai_intel_dashboard.src.infrastructure.config")
    config_pkg.__path__ = [
        str(
            PROJECT_ROOT / "yosai_intel_dashboard" / "src" / "infrastructure" / "config"
        )
    ]
    sys.modules.setdefault(
        "yosai_intel_dashboard.src.infrastructure.config", config_pkg
    )

    services_db_pkg = _simple_module("yosai_intel_dashboard.src.services.database")
    services_db_pkg.__path__ = [
        str(PROJECT_ROOT / "yosai_intel_dashboard" / "src" / "database")
    ]
    sys.modules.setdefault(
        "yosai_intel_dashboard.src.services.database", services_db_pkg
    )

    services_pkg = importlib.import_module("services")
    analytics_mod = importlib.import_module("analytics")
    sys.modules.setdefault("services.analytics", analytics_mod)
    setattr(services_pkg, "analytics", analytics_mod)

    sys.modules.setdefault(
        "services.analytics.core", importlib.import_module("analytics.core")
    )
    sys.modules.setdefault(
        "services.analytics.core.utils",
        importlib.import_module("analytics.core.utils"),
    )
    sys.modules.setdefault(
        "services.analytics.core.callbacks",
        importlib.import_module("analytics.core.callbacks"),
    )
    sys.modules.setdefault(
        "services.analytics.security_patterns",
        importlib.import_module("analytics.security_patterns"),
    )
    sys.modules.setdefault(
        "services.analytics.security_patterns.pattern_detection",
        importlib.import_module("analytics.security_patterns.pattern_detection"),
    )
    try:  # pragma: no cover - optional graph dependencies
        sys.modules.setdefault(
            "services.analytics.graph_analysis",
            importlib.import_module("analytics.graph_analysis"),
        )
        sys.modules.setdefault(
            "services.analytics.graph_analysis.algorithms",
            importlib.import_module("analytics.graph_analysis.algorithms"),
        )
    except Exception:  # pragma: no cover
        sys.modules.setdefault(
            "services.analytics.graph_analysis",
            types.ModuleType("services.analytics.graph_analysis"),
        )
        sys.modules.setdefault(
            "services.analytics.graph_analysis.algorithms",
            types.ModuleType("services.analytics.graph_analysis.algorithms"),
        )

    class _MockConnection:
        def __init__(self):
            self._connected = True

        def health_check(self):
            return self._connected

        def close(self):
            self._connected = False

    db_manager_stub = _simple_module(
        "yosai_intel_dashboard.src.infrastructure.config.database_manager",
        MockConnection=_MockConnection,
    )
    sys.modules.setdefault(
        "yosai_intel_dashboard.src.infrastructure.config.database_manager",
        db_manager_stub,
    )


# Run configuration steps on import
set_test_environment()
add_project_root_to_sys_path()
register_dependency_stubs()

from .fake_configuration import FakeConfiguration  # noqa: E402,F401


# ---------------------------------------------------------------------------
# Fixtures
@pytest.fixture
def temp_dir(tmp_path):
    """Provide a temporary directory path."""
    return tmp_path


@pytest.fixture
def fake_unicode_processor():
    """Return the reusable fake unicode processor."""
    from .fake_unicode_processor import FakeUnicodeProcessor

    return FakeUnicodeProcessor()


@pytest.fixture
def stub_services_registry():
    """Provide a lightweight stub for the optional service registry."""
    import types
    import sys

    stub = types.ModuleType("core.registry")
    stub.ServiceRegistry = type("ServiceRegistry", (), {})
    stub.ServiceDiscovery = type(
        "ServiceDiscovery", (), {"resolve": lambda self, name: None}
    )
    stub.registry = object()
    stub.register_service = lambda *a, **k: None
    stub.get_service = lambda *a, **k: None
    stub.register_builtin_services = lambda: None
    sys.modules["core.registry"] = stub
    # Provide legacy alias for compatibility
    sys.modules["services.registry"] = stub
    try:
        yield stub
    finally:
        sys.modules.pop("core.registry", None)
        sys.modules.pop("services.registry", None)
