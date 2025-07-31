#!/usr/bin/env python3
"""Helpers for analytics summary and service status."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class SummaryReporter:
    """Provide reporting helpers for analytics service."""

    def __init__(self, database_manager: Any):
        self.database_manager = database_manager

    def health_check(self) -> Dict[str, Any]:
        """Check service health."""
        health: Dict[str, Any] = {
            "service": "healthy",
            "timestamp": datetime.now().isoformat(),
        }
        if self.database_manager:
            try:
                health["database"] = (
                    "healthy" if self.database_manager.health_check() else "unhealthy"
                )
            except Exception:
                health["database"] = "unhealthy"
        else:
            health["database"] = "not_configured"

        try:
            from yosai_intel_dashboard.src.core.interfaces.service_protocols import get_upload_data_service
            from services.upload_data_service import get_uploaded_filenames

            health["uploaded_files"] = len(
                get_uploaded_filenames(get_upload_data_service())
            )
        except ImportError:
            health["uploaded_files"] = "not_available"
        return health

    def get_data_source_options(self) -> List[Dict[str, str]]:
        """Return available data source options."""
        options = [{"label": "Sample Data", "value": "sample"}]
        try:
            from yosai_intel_dashboard.src.core.interfaces.service_protocols import get_upload_data_service
            from services.upload_data_service import get_uploaded_filenames

            uploaded_files = get_uploaded_filenames(get_upload_data_service())
            if uploaded_files:
                options.append(
                    {
                        "label": f"Uploaded Files ({len(uploaded_files)})",
                        "value": "uploaded",
                    }
                )
        except ImportError:
            pass
        if self.database_manager and self.database_manager.health_check():
            options.append({"label": "Database", "value": "database"})
        return options

    def get_available_sources(self) -> List[str]:
        """Return identifiers for available data sources."""
        return [opt.get("value", "") for opt in self.get_data_source_options()]

    def get_date_range_options(self) -> Dict[str, str]:
        """Get default date range options."""
        return {
            "start": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
            "end": datetime.now().strftime("%Y-%m-%d"),
        }

    def get_analytics_status(self) -> Dict[str, Any]:
        """Return current analytics status."""
        status = {
            "timestamp": datetime.now().isoformat(),
            "data_sources_available": len(self.get_data_source_options()),
            "service_health": self.health_check(),
        }
        try:
            from yosai_intel_dashboard.src.core.interfaces.service_protocols import get_upload_data_service
            from services.upload_data_service import get_uploaded_filenames

            status["uploaded_files"] = len(
                get_uploaded_filenames(get_upload_data_service())
            )
        except ImportError:
            status["uploaded_files"] = 0
        return status


__all__ = ["SummaryReporter"]
