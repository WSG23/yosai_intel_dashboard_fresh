"""Pytest configuration for the test-suite."""

from __future__ import annotations

import importlib.util
import os
import resource
import sys
import warnings
from contextlib import contextmanager
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Callable, Iterator, List
from unittest import mock
import builtins
import requests

# Make project package importable
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from yosai_intel_dashboard.src.core.imports import (
    fallbacks as _fallbacks,
)  # noqa: F401,E402

import pytest  # noqa: E402

from yosai_intel_dashboard.src.database.types import DatabaseConnection  # noqa: E402

try:
    from memory_profiler import memory_usage  # type: ignore

    if not callable(memory_usage):  # handle older or module-style imports
        memory_usage = None  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    memory_usage = None  # type: ignore

pytest_plugins = []


def _register_stub(module_name: str, module: ModuleType | None = None) -> ModuleType:
    """Install ``module`` as a lightweight stub under ``module_name``."""
    if module is None:
        module = ModuleType(module_name.split(".")[-1])
    sys.modules[module_name] = module
    return module


@pytest.fixture
def stub_services_registry():
    """Provide a lightweight stub for the optional service registry."""
    import types

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
    sys.modules["services.registry"] = stub
    try:
        yield stub
    finally:
        sys.modules.pop("core.registry", None)
        sys.modules.pop("services.registry", None)


for _mod, _stub in [
    ("prometheus_client", ModuleType("prometheus_client")),
    ("prometheus_fastapi_instrumentator", None),
    ("redis", None),
    ("opentelemetry", None),
    ("opentelemetry.context", None),
    ("opentelemetry.propagate", None),
    ("opentelemetry.trace", None),
    ("opentelemetry.sdk", None),
    ("opentelemetry.sdk.resources", None),
    ("opentelemetry.sdk.trace", None),
    ("opentelemetry.sdk.trace.export", None),
    ("opentelemetry.exporter.jaeger.thrift", None),
    ("opentelemetry.instrumentation.fastapi", None),
    ("structlog", None),
    ("sklearn", None),
    ("sklearn.ensemble", SimpleNamespace(IsolationForest=object())),
    (
        "yosai_intel_dashboard.src.infrastructure.security.query_builder",
        SimpleNamespace(log_sanitized_query=lambda *a, **k: None),
    ),
    (
        "yosai_intel_dashboard.src.infrastructure.security.unicode_security_validator",
        SimpleNamespace(
            UnicodeSecurityValidator=type(
                "UnicodeSecurityValidator",
                (),
                {"validate_and_sanitize": lambda self, text: text},
            )
        ),
    ),
]:
    if _mod == "prometheus_client":

        class _Metric:
            def __init__(self, *a, **k):
                pass

            def labels(self, *a, **k):
                return self

            def inc(self, *a, **k):
                pass

            def observe(self, *a, **k):
                pass

            def set(self, *a, **k):
                pass

        _stub.Counter = _Metric
        _stub.Gauge = _Metric
        _stub.Histogram = _Metric
        _stub.REGISTRY = SimpleNamespace(_names_to_collectors={})
    _register_stub(_mod, _stub)


@pytest.fixture(scope="session", autouse=True)
def auto_stub_dependencies() -> Callable[[str, ModuleType | None], ModuleType]:
    """Register additional optional dependency stubs for tests.

    Tests can request this fixture and call it with a module name and
    optional ``ModuleType`` instance to make the stub available for the
    duration of the test session.
    """

    return _register_stub


DatabaseConnectionFactory = Callable[[], Iterator[DatabaseConnection]]


def _close_pool(pool) -> None:
    """Close all connections in the given pool."""
    while pool._pool:
        conn, _ = pool._pool.pop()
        conn.close()


_missing_packages = [
    pkg for pkg in ("yaml", "psutil") if importlib.util.find_spec(pkg) is None
]
if _missing_packages:
    warnings.warn(
        "Missing required test dependencies: " + ", ".join(_missing_packages),
        RuntimeWarning,
    )


DEFAULT_MAX_MEMORY_MB = int(os.environ.get("PYTEST_MAX_MEMORY_MB", "512"))


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Purge project modules from ``sys.modules`` before each test."""
    prefix = "yosai_intel_dashboard"
    for name in [m for m in list(sys.modules) if m.startswith(prefix)]:
        sys.modules.pop(name, None)
    yield
    for name in [m for m in list(sys.modules) if m.startswith(prefix)]:
        sys.modules.pop(name, None)


@pytest.fixture(autouse=True)
def profile_and_limit_memory(request):
    """Profile memory usage and enforce per-test memory caps."""
    max_mb = DEFAULT_MAX_MEMORY_MB
    marker = request.node.get_closest_marker("memlimit")
    if marker and marker.args:
        try:
            max_mb = int(marker.args[0])
        except (TypeError, ValueError):  # pragma: no cover - defensive
            pass
    soft, hard = resource.getrlimit(resource.RLIMIT_AS)
    limit_bytes = max_mb * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (limit_bytes, hard))
    before = memory_usage(-1, max_iterations=1)[0] if memory_usage else None
    try:
        yield
    finally:
        after = memory_usage(-1, max_iterations=1)[0] if memory_usage else None
        if before is not None and after is not None:
            print(f"[mem] {request.node.nodeid}: {before:.1f} -> {after:.1f} MiB")
        resource.setrlimit(resource.RLIMIT_AS, (soft, hard))


@pytest.fixture
def temp_dir(tmp_path_factory):
    """Provide a temporary directory unique to each test."""
    return tmp_path_factory.mktemp("tmp")


@pytest.fixture
def di_container():
    """Simple dependency injection container instance."""
    from yosai_intel_dashboard.src.infrastructure.di.service_container import (
        ServiceContainer,
    )

    return ServiceContainer()


@pytest.fixture
def fake_unicode_processor():
    """Fixture returning a ``FakeUnicodeProcessor`` instance."""
    from .fake_unicode_processor import FakeUnicodeProcessor

    return FakeUnicodeProcessor()


@pytest.fixture
def mock_db_connection():
    """Reusable mock database connection."""
    conn = mock.Mock()
    conn.health_check.return_value = True
    return conn


@pytest.fixture
def mock_analytics_processor():
    """Fixture returning an ``UploadAnalyticsProcessor`` instance."""
    from validation.security_validator import SecurityValidator
    from yosai_intel_dashboard.src.core.events import EventBus
    from yosai_intel_dashboard.src.infrastructure.callbacks.unified_callbacks import (
        TrulyUnifiedCallbacks,
    )
    from yosai_intel_dashboard.src.infrastructure.config.dynamic_config import (
        dynamic_config,
    )
    from yosai_intel_dashboard.src.services.analytics.upload_analytics import (
        UploadAnalyticsProcessor,
    )
    from yosai_intel_dashboard.src.services.data_processing.processor import Processor

    vs = SecurityValidator()
    processor = Processor(validator=vs)
    event_bus = EventBus()
    callbacks = TrulyUnifiedCallbacks(event_bus=event_bus, security_validator=vs)
    return UploadAnalyticsProcessor(
        vs, processor, callbacks, dynamic_config.analytics, event_bus
    )


@pytest.fixture
def mock_db_factory() -> Iterator[DatabaseConnectionFactory]:
    """Factory yielding connections to the in-memory mock database.

    Use as::

        with mock_db_factory() as conn:
            ...
    """

    from yosai_intel_dashboard.src.infrastructure.config.connection_pool import (
        DatabaseConnectionPool,
    )
    from yosai_intel_dashboard.src.infrastructure.config.database_manager import (
        ThreadSafeDatabaseManager,
    )
    from yosai_intel_dashboard.src.infrastructure.config.schema import DatabaseSettings

    config = DatabaseSettings(type="mock")
    manager = ThreadSafeDatabaseManager(config)
    pool = DatabaseConnectionPool(manager._create_connection, 1, 2, 30, 1)
    checked_out: List[DatabaseConnection] = []

    @contextmanager
    def factory() -> Iterator[DatabaseConnection]:
        conn = pool.get_connection()
        checked_out.append(conn)
        try:
            yield conn
        finally:
            checked_out.remove(conn)
            pool.release_connection(conn)

    yield factory

    for conn in list(checked_out):
        try:
            pool.release_connection(conn)
        except Exception:
            pass
    _close_pool(pool)
    manager.close()


@pytest.fixture
def sqlite_connection_factory(
    tmp_path,
) -> Iterator[DatabaseConnectionFactory]:
    """Factory yielding SQLite connections backed by a temporary file.

    Use as::

        with sqlite_connection_factory() as conn:
            conn.execute_query("SELECT 1")
    """

    from yosai_intel_dashboard.src.infrastructure.config.connection_pool import (
        DatabaseConnectionPool,
    )
    from yosai_intel_dashboard.src.infrastructure.config.database_manager import (
        ThreadSafeDatabaseManager,
    )
    from yosai_intel_dashboard.src.infrastructure.config.schema import DatabaseSettings

    db_path = tmp_path / "test.db"
    config = DatabaseSettings(type="sqlite", name=str(db_path))
    manager = ThreadSafeDatabaseManager(config)
    pool = DatabaseConnectionPool(manager._create_connection, 1, 2, 30, 1)
    checked_out: List[DatabaseConnection] = []

    @contextmanager
    def factory() -> Iterator[DatabaseConnection]:
        conn = pool.get_connection()
        checked_out.append(conn)
        try:
            yield conn
        finally:
            checked_out.remove(conn)
            pool.release_connection(conn)

    yield factory

    for conn in list(checked_out):
        try:
            pool.release_connection(conn)
        except Exception:
            pass
    _close_pool(pool)
    manager.close()


@pytest.fixture
def postgres_connection_factory() -> Iterator[DatabaseConnectionFactory]:
    """Factory yielding PostgreSQL connections using ``testcontainers``.

    This fixture requires the ``testcontainers`` package. Use as::

        with postgres_connection_factory() as conn:
            conn.execute_query("SELECT 1")
    """

    pytest.importorskip("testcontainers.postgres")
    from testcontainers.postgres import PostgresContainer

    from yosai_intel_dashboard.src.infrastructure.config.connection_pool import (
        DatabaseConnectionPool,
    )
    from yosai_intel_dashboard.src.infrastructure.config.database_manager import (
        ThreadSafeDatabaseManager,
    )
    from yosai_intel_dashboard.src.infrastructure.config.schema import DatabaseSettings

    with PostgresContainer("postgres:15-alpine") as pg:
        config = DatabaseSettings(
            type="postgresql",
            host=pg.get_container_host_ip(),
            port=int(pg.get_exposed_port(5432)),
            name=pg.dbname,
            user=pg.username,
            password=pg.password,
        )
        manager = ThreadSafeDatabaseManager(config)
        pool = DatabaseConnectionPool(manager._create_connection, 1, 2, 30, 1)
        checked_out: List[DatabaseConnection] = []

        @contextmanager
        def factory() -> Iterator[DatabaseConnection]:
            conn = pool.get_connection()
            checked_out.append(conn)
            try:
                yield conn
            finally:
                checked_out.remove(conn)
                pool.release_connection(conn)

        yield factory

        for conn in list(checked_out):
            try:
                pool.release_connection(conn)
            except Exception:
                pass
        _close_pool(pool)
        manager.close()


@pytest.fixture(autouse=True)
def mock_network_and_files(monkeypatch, tmp_path, request):
    """Disable real network calls and restrict file writes in unit tests.

    Integration tests opt-out by using the ``integration`` marker.
    """
    if "integration" in request.keywords:
        return

    def _blocked(*_a, **_k):
        raise RuntimeError("Network access disabled during unit tests")

    try:
        monkeypatch.setattr(requests.sessions.Session, "request", _blocked)
    except Exception:
        pass

    original_open = builtins.open

    def _safe_open(file, mode="r", *args, **kwargs):
        if any(m in mode for m in ("w", "a", "x")):
            path = Path(file).resolve()
            if not str(path).startswith(str(tmp_path)):
                raise RuntimeError("File write outside tmp path disabled in unit tests")
        return original_open(file, mode, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", _safe_open)
