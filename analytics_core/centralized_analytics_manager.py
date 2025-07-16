from __future__ import annotations

"""Lightweight centralized analytics manager coordinating sub services."""

from dataclasses import dataclass, field
from typing import Any

from .callbacks.unified_callback_manager import UnifiedCallbackManager


@dataclass
class CentralizedAnalyticsManager:
    """Aggregate analytics services behind a simple interface."""

    core_service: Any | None = None
    ai_service: Any | None = None
    performance_service: Any | None = None
    data_service: Any | None = None
    callback_manager: UnifiedCallbackManager = field(
        default_factory=UnifiedCallbackManager
    )

    def run_full_pipeline(self, data: Any) -> None:
        """Run the full analytics pipeline on ``data``."""
        if self.core_service:
            self.core_service.process(data)
        if self.ai_service:
            self.ai_service.analyze(data)
        if self.performance_service:
            self.performance_service.profile(data)
        if self.data_service:
            self.data_service.transform(data)
        self.callback_manager.trigger("pipeline_complete", data)


__all__ = ["CentralizedAnalyticsManager"]
