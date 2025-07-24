from __future__ import annotations

from typing import Any, Optional

from core.truly_unified_callbacks import TrulyUnifiedCallbacks
from .ui_component import UIComponent


class StreamlinedComponent(UIComponent):
    """Base class for UI components using TrulyUnifiedCallbacks."""

    def register_callbacks(
        self, manager: TrulyUnifiedCallbacks, controller: Any | None = None
    ) -> None:
        """Register Dash callbacks for the component."""
        return None
