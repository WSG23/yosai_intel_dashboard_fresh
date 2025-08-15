import pytest
from types import SimpleNamespace, ModuleType
import sys


def test_mock_db_enabled(monkeypatch):
    """Factory uses MockDatabaseManager when USE_MOCK_DB is set."""
    monkeypatch.setenv("USE_MOCK_DB", "1")
    monkeypatch.setenv("CACHE_TTL_SECONDS", "1")
    monkeypatch.setenv("JWKS_CACHE_TTL", "1")
    dummy_perf = ModuleType("performance")
    dummy_perf.cache_monitor = None
    dummy_perf.MetricType = type("MetricType", (), {})
    dummy_perf.PerformanceThresholds = type(
        "PerformanceThresholds", (), {"SLOW_QUERY_SECONDS": 1}
    )
    dummy_perf.get_performance_monitor = lambda: type(
        "Monitor", (), {"record_metric": lambda *a, **k: None}
    )()
    monkeypatch.setitem(
        sys.modules, "yosai_intel_dashboard.src.core.performance", dummy_perf
    )

    from yosai_intel_dashboard.src.core.plugins.config.factories import (
        DatabaseManagerFactory,
    )
    from yosai_intel_dashboard.src.core.plugins.config.database_manager import (
        MockDatabaseManager,
    )

    config = SimpleNamespace(type="postgresql")
    manager = DatabaseManagerFactory.create_manager(config)
    assert isinstance(manager, MockDatabaseManager)


def test_mock_db_disabled(monkeypatch):
    """Factory falls back to SQLite when USE_MOCK_DB is not set."""
    monkeypatch.delenv("USE_MOCK_DB", raising=False)
    monkeypatch.setenv("CACHE_TTL_SECONDS", "1")
    monkeypatch.setenv("JWKS_CACHE_TTL", "1")
    dummy_perf = ModuleType("performance")
    dummy_perf.cache_monitor = None
    dummy_perf.MetricType = type("MetricType", (), {})
    dummy_perf.PerformanceThresholds = type(
        "PerformanceThresholds", (), {"SLOW_QUERY_SECONDS": 1}
    )
    dummy_perf.get_performance_monitor = lambda: type(
        "Monitor", (), {"record_metric": lambda *a, **k: None}
    )()
    monkeypatch.setitem(
        sys.modules, "yosai_intel_dashboard.src.core.performance", dummy_perf
    )

    from yosai_intel_dashboard.src.core.plugins.config.factories import (
        DatabaseManagerFactory,
    )
    from yosai_intel_dashboard.src.core.plugins.config.database_manager import (
        SQLiteDatabaseManager,
    )

    config = SimpleNamespace(type="sqlite")
    manager = DatabaseManagerFactory.create_manager(config)
    assert isinstance(manager, SQLiteDatabaseManager)
