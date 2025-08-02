from __future__ import annotations

from datetime import datetime
from typing import Optional

from .timescale.manager import TimescaleDBManager


class ModelMonitoringService:
    """Service for logging model evaluation metrics to TimescaleDB."""

    def __init__(self, manager: TimescaleDBManager | None = None) -> None:
        self.manager = manager or TimescaleDBManager()

    async def log_evaluation(
        self,
        model_name: str,
        version: str,
        metric: str,
        value: float,
        drift_type: str,
        status: str,
        *,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """Record an evaluation result in TimescaleDB."""
        ts = timestamp or datetime.utcnow()
        await self.manager.fetch(
            """
            INSERT INTO model_monitoring_events (
                time, model_name, version, metric, value, drift_type, status
            ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            ts,
            model_name,
            version,
            metric,
            value,
            drift_type,
            status,
        )

