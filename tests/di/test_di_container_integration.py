from core.container import Container

from config import create_config_manager
from services.analytics_service import AnalyticsService


def test_container_initializes_without_circular_dependencies():
    container = Container()
    cfg = create_config_manager()
    analytics = AnalyticsService()

    container.register("config", cfg)
    container.register("analytics", analytics)

    assert container.get("config") is cfg
    assert container.get("analytics") is analytics
