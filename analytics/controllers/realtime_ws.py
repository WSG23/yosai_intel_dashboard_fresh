from __future__ import annotations

"""Controller utilities for real-time websocket data."""

import json
import logging
from typing import Any, Dict, Optional

from components import create_analytics_charts, create_summary_cards

logger = logging.getLogger(__name__)


class RealTimeWebSocketController:
    """Handle incoming websocket messages and map to UI components."""

    def parse_message(
        self, message: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Return parsed JSON payload from a websocket ``message``."""
        if not message:
            return None
        try:
            return json.loads(message.get("data", "{}"))
        except Exception:  # pragma: no cover - invalid message
            logger.error("Failed parsing websocket message: %s", message)
            return None

    # ------------------------------------------------------------------
    def create_summary(self, data: Optional[Dict[str, Any]]) -> Any:
        """Return summary card components from ``data``."""
        if not data:
            return None
        return create_summary_cards(data)

    # ------------------------------------------------------------------
    def create_charts(self, data: Optional[Dict[str, Any]]) -> Any:
        """Return analytics chart components from ``data``."""
        if not data:
            return None
        return create_analytics_charts(data)


__all__ = ["RealTimeWebSocketController"]
