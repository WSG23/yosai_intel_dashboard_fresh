from yosai_intel_dashboard.src.infrastructure.config.database_manager import DatabaseSettings, EnhancedPostgreSQLManager


def test_query_metrics_collected_for_multiple_queries():
    cfg = DatabaseSettings(type="mock")
    manager = EnhancedPostgreSQLManager(cfg)

    manager.execute_query_with_retry("SELECT 1")
    manager.execute_query_with_retry("SELECT 2")

    metrics = manager.performance_analyzer.query_metrics
    assert len(metrics) == 2
    assert metrics[0]["query"] == "SELECT 1"
    assert metrics[1]["query"] == "SELECT 2"
    assert metrics[0]["execution_time"] >= 0
    assert metrics[1]["execution_time"] >= 0
