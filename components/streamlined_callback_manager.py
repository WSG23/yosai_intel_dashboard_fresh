from __future__ import annotations

from typing import Any

from yosai_intel_dashboard.src.core.truly_unified_callbacks import TrulyUnifiedCallbacks

from .streamlined_component import StreamlinedComponent


class StreamlinedCallbackManager:
    """Helper to register callbacks for StreamlinedComponents."""

    def __init__(self, manager: TrulyUnifiedCallbacks) -> None:
        self.manager = manager

    def register_component(
        self, component: StreamlinedComponent, controller: Any | None = None
    ) -> None:
        component.register_callbacks(self.manager, controller)
