from analytics_core.centralized_analytics_manager import (
    CentralizedAnalyticsManager,
)
from analytics_core.services.ai_service import AIAnalyticsService
from analytics_core.services.core_service import CoreAnalyticsService
from analytics_core.services.data_processing_service import DataProcessingService
from analytics_core.services.performance_service import PerformanceAnalyticsService
from core.service_container import ServiceContainer


class DatabaseManager:
    pass


def test_service_container_example():
    container = ServiceContainer()
    container.register_singleton("db", DatabaseManager)
    assert container.has("db")
    db = container.get("db")
    assert isinstance(db, DatabaseManager)


def test_centralized_analytics_manager_example():
    manager = CentralizedAnalyticsManager(
        core_service=CoreAnalyticsService(),
        ai_service=AIAnalyticsService(),
        performance_service=PerformanceAnalyticsService(),
        data_service=DataProcessingService(),
    )
    manager.run_full_pipeline({"sample": 123})
