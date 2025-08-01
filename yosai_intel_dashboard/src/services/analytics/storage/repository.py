from __future__ import annotations

"""Database repository for analytics."""

from typing import Any, Dict

from yosai_intel_dashboard.src.services.db_analytics_helper import DatabaseAnalyticsHelper


class AnalyticsRepository:
    """Provide access to analytics stored in a database."""

    def __init__(self, helper: DatabaseAnalyticsHelper) -> None:
        self.helper = helper

    def get_analytics(self) -> Dict[str, Any]:
        return self.helper.get_analytics()


__all__ = ["AnalyticsRepository"]
