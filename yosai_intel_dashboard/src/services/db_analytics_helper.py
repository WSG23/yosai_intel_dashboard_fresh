#!/usr/bin/env python3
"""Wrapper around DatabaseAnalyticsService for composition."""

from __future__ import annotations

from typing import Any, Dict

from .database_analytics_service import DatabaseAnalyticsService


class DatabaseAnalyticsHelper:
    """Thin wrapper delegating to :class:`DatabaseAnalyticsService`."""

    def __init__(self, database_manager: Any):
        self.service = (
            DatabaseAnalyticsService(database_manager) if database_manager else None
        )

    def get_analytics(self) -> Dict[str, Any]:
        if not self.service:
            return {"status": "error", "message": "Database not available"}
        return self.service.get_analytics()


__all__ = ["DatabaseAnalyticsHelper"]
