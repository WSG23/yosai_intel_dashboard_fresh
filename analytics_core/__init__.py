"""Centralized analytics package."""

from .centralized_analytics_manager import CentralizedAnalyticsManager


def create_manager() -> CentralizedAnalyticsManager:
    """Factory returning a centralized analytics manager."""
    return CentralizedAnalyticsManager()

__all__ = ["CentralizedAnalyticsManager", "create_manager"]
