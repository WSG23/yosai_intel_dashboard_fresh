"""Basic DI container performance monitoring."""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, Optional

from .base_model import BaseModel


@dataclass
class ServiceMetrics:
    total_resolutions: int = 0
    total_time: float = 0.0
    average_time: float = 0.0
    errors: int = 0
    last_resolution_time: float = 0.0


class DIPerformanceMonitor(BaseModel):
    """Monitor performance of service resolution."""

    def __init__(
        self,
        config: Optional[Any] = None,
        db: Optional[Any] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        super().__init__(config, db, logger)
        self.service_metrics: Dict[str, ServiceMetrics] = defaultdict(ServiceMetrics)

    def record_service_resolution(
        self, service_key: str, resolution_time: float
    ) -> None:
        metrics = self.service_metrics[service_key]
        metrics.total_resolutions += 1
        metrics.total_time += resolution_time
        metrics.average_time = metrics.total_time / metrics.total_resolutions
        metrics.last_resolution_time = resolution_time

    def record_service_error(self, service_key: str, _error: str) -> None:
        metrics = self.service_metrics[service_key]
        metrics.errors += 1

    def get_metrics_summary(self) -> Dict[str, Any]:
        return {key: vars(value) for key, value in self.service_metrics.items()}
