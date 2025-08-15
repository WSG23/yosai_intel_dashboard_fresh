from yosai_intel_dashboard.src.services.analytics.core import create_manager
from yosai_intel_dashboard.src.infrastructure.di.service_container import ServiceContainer


class DatabaseManager:
    pass


def test_service_container_example():
    container = ServiceContainer()
    container.register_singleton("db", DatabaseManager)
    assert container.has("db")
    db = container.get("db")
    assert isinstance(db, DatabaseManager)


def test_centralized_analytics_manager_example():
    manager = create_manager()
    manager.run_full_pipeline({"sample": 123})
