#!/usr/bin/env python3
"""Helpers for analytics summary and result formatting."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

from yosai_intel_dashboard.src.core.interfaces.service_protocols import (
    UploadDataServiceProtocol,
    get_upload_data_service,
)

logger = logging.getLogger(__name__)


class SummaryReporter:
    """Provide reporting helpers for analytics service."""

    def __init__(
        self,
        database_manager: Any,
        upload_service: UploadDataServiceProtocol | None = None,
    ) -> None:
        self.database_manager = database_manager
        self.upload_service = upload_service or get_upload_data_service()

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
            health["uploaded_files"] = len(
                self.upload_service.get_uploaded_filenames()
            )
        except Exception:
            health["uploaded_files"] = "not_available"
        return health

    def get_data_source_options(self) -> List[Dict[str, str]]:
        """Return available data source options."""
        options = [{"label": "Sample Data", "value": "sample"}]
        try:
            uploaded_files = self.upload_service.get_uploaded_filenames()
            if uploaded_files:
                options.append(
                    {
                        "label": f"Uploaded Files ({len(uploaded_files)})",
                        "value": "uploaded",
                    }
                )
        except Exception:
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
            status["uploaded_files"] = len(
                self.upload_service.get_uploaded_filenames()
            )
        except Exception:
            status["uploaded_files"] = 0
        return status


def format_patterns_result(
    total_records: int,
    unique_users: int,
    unique_devices: int,
    date_span: int,
    power_users: List[str],
    regular_users: List[str],
    occasional_users: List[str],
    high_traffic: List[str],
    moderate_traffic: List[str],
    low_traffic: List[str],
    total_interactions: int,
    success_rate: float,
) -> Dict[str, Any]:
    """Build the final unique patterns analysis result."""
    return {
        "status": "success",
        "analysis_timestamp": datetime.now().isoformat(),
        "data_summary": {
            "total_records": total_records,
            "unique_entities": {
                "users": unique_users,
                "devices": unique_devices,
                "interactions": total_interactions,
            },
            "date_range": {"span_days": date_span},
        },
        "user_patterns": {
            "total_unique_users": unique_users,
            "user_classifications": {
                "power_users": power_users[:10],
                "regular_users": regular_users[:10],
                "occasional_users": occasional_users[:10],
            },
        },
        "device_patterns": {
            "total_unique_devices": unique_devices,
            "device_classifications": {
                "high_traffic_devices": high_traffic[:10],
                "moderate_traffic_devices": moderate_traffic[:10],
                "low_traffic_devices": low_traffic[:10],
                "secure_devices": [],
                "popular_devices": high_traffic[:5],
                "problematic_devices": [],
            },
        },
        "interaction_patterns": {
            "total_unique_interactions": total_interactions,
            "interaction_statistics": {"unique_pairs": total_interactions},
        },
        "temporal_patterns": {"date_span_days": date_span},
        "access_patterns": {
            "overall_success_rate": success_rate,
            "success_percentage": success_rate * 100,
        },
        "recommendations": [],
    }


__all__ = ["SummaryReporter", "format_patterns_result"]
