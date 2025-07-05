from __future__ import annotations

"""UI controller that exposes analytics operations to the presentation layer."""

from typing import Any, Dict, Optional

from core.callback_manager import CallbackManager
from core.callback_events import CallbackEvent

from .business_service import AnalyticsBusinessService


class AnalyticsUIController:
    """Coordinate UI requests with the business service and callbacks."""

    def __init__(
        self,
        service: AnalyticsBusinessService,
        callback_manager: Optional[CallbackManager] = None,
    ) -> None:
        self.service = service
        self.callback_manager = callback_manager or CallbackManager()

    # ------------------------------------------------------------------
    def handle_analysis_request(self, ui_data: Any) -> Dict[str, Any]:
        """Process a UI request for analytics and return formatted results."""
        self.callback_manager.trigger(CallbackEvent.ANALYSIS_START, "ui", {})
        results = self.service.run_analysis(ui_data)
        formatted = self.format_results_for_ui(results)
        self.callback_manager.trigger(
            CallbackEvent.ANALYSIS_COMPLETE, "ui", formatted
        )
        return formatted

    # ------------------------------------------------------------------
    def format_results_for_ui(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Return results in a structure suitable for UI consumption."""
        return dict(results)
