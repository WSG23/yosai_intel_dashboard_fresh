from core.container import Container

from config.config import ConfigManager
from services.analytics_service import AnalyticsService


def test_container_initializes_without_circular_dependencies():
    container = Container()
    cfg = ConfigManager()
    analytics = AnalyticsService()

    container.register("config", cfg)
    container.register("analytics", analytics)

    assert container.get("config") is cfg
    assert container.get("analytics") is analytics
