import pytest

from yosai_intel_dashboard.src.core.plugins.performance_manager import PluginPerformanceManager
from tools.migration_validator import (
    MigrationValidator,
    test_migration_equivalence,
    test_migration_performance,
    test_migration_security,
)


@pytest.mark.performance
def test_plugin_performance_tracking():
    mgr = PluginPerformanceManager()
    mgr.record_plugin_metric("plug", "load_time", 1.0)
    metrics = mgr.analyze_plugin_performance("plug")
    assert metrics["load_time"] == 1.0


def test_migration_detection():
    validator = MigrationValidator()
    assert validator.generate_validation_report()["status"] == "ok"


@pytest.mark.performance
def test_performance_alerts():
    mgr = PluginPerformanceManager()
    mgr.performance_thresholds["load_time"] = 0.5
    mgr.record_plugin_metric("plug", "load_time", 1.0)
    alerts = mgr.detect_performance_issues()
    assert alerts and alerts[0]["plugin"] == "plug"
