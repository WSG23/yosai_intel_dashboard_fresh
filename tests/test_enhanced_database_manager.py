from yosai_intel_dashboard.src.infrastructure.config.database_manager import DatabaseSettings, EnhancedPostgreSQLManager


def test_execute_query_with_retry(monkeypatch):
    cfg = DatabaseSettings(type="mock")
    manager = EnhancedPostgreSQLManager(cfg)

    result = manager.execute_query_with_retry("SELECT 1")
    assert result == [{"id": 1, "result": "mock_data"}]


def test_health_check_with_retry(monkeypatch):
    cfg = DatabaseSettings(type="mock")
    manager = EnhancedPostgreSQLManager(cfg)
    assert manager.health_check_with_retry() is True
