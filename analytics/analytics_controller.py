"""Compatibility wrapper for the analytics subsystem."""

from __future__ import annotations

from typing import Any, Dict, Optional

from analytics_core.callbacks.unified_callback_manager import CallbackManager

from .business_service import AnalyticsBusinessService
from .data_repository import AnalyticsDataRepository
from .ui_controller import AnalyticsUIController


class AnalyticsController(AnalyticsUIController):
    """Backward compatible controller that delegates to :class:`AnalyticsUIController`."""

    def __init__(
        self,
        repository: Optional[AnalyticsDataRepository] = None,
        callback_manager: Optional[CallbackManager] = None,
    ) -> None:
        repository = repository or AnalyticsDataRepository()
        service = AnalyticsBusinessService(repository)
        super().__init__(service, callback_manager)

    def analyze(self, criteria: Any) -> Dict[str, Any]:
        """Compatibility method forwarding to :meth:`handle_analysis_request`."""
        return self.handle_analysis_request(criteria)


__all__ = ["AnalyticsController"]
