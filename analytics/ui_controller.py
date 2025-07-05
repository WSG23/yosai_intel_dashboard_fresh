from __future__ import annotations

"""UI controller that exposes analytics operations to the presentation layer."""

from typing import Any, Dict, Optional

from services.data_processing.callback_controller import (
    CallbackController,
    CallbackEvent,
)

from .business_service import AnalyticsBusinessService


class AnalyticsUIController:
    """Coordinate UI requests with the business service and callbacks."""

    def __init__(
        self,
        service: AnalyticsBusinessService,
        callback_controller: Optional[CallbackController] = None,
    ) -> None:
        self.service = service
        self.callback_controller = callback_controller or CallbackController()

    # ------------------------------------------------------------------
    def handle_analysis_request(self, ui_data: Any) -> Dict[str, Any]:
        """Process a UI request for analytics and return formatted results."""
        self.callback_controller.fire_event(CallbackEvent.ANALYSIS_START, "ui", {})
        results = self.service.run_analysis(ui_data)
        formatted = self.format_results_for_ui(results)
        self.callback_controller.fire_event(
            CallbackEvent.ANALYSIS_COMPLETE, "ui", formatted
        )
        return formatted

    # ------------------------------------------------------------------
    def format_results_for_ui(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Return results in a structure suitable for UI consumption."""
        return dict(results)
