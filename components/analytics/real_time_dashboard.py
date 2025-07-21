from __future__ import annotations

from dash import html

from core.truly_unified_callbacks import TrulyUnifiedCallbacks


class RealTimeAnalytics:
    """Dashboard component updating via WebSocket."""

    def __init__(self, url: str = "ws://localhost:6789", interval: int = 1000) -> None:
        self.url = url
        self.interval = interval
        
    def layout(self) -> html.Div:
        """Return a placeholder div for mounting the React dashboard."""
        return html.Div(id="real-time-root")

    def register_callbacks(self, manager: TrulyUnifiedCallbacks) -> None:
        """React-based dashboard requires no Dash callbacks."""
        return None



__all__ = ["RealTimeAnalytics"]
