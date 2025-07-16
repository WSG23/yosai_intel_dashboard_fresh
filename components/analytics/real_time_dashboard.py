from __future__ import annotations

from typing import Any

from dash import dcc, html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from dash_extensions import WebSocket

from analytics.controllers.realtime_ws import RealTimeWebSocketController
from core.truly_unified_callbacks import TrulyUnifiedCallbacks


class RealTimeAnalytics:
    """Dashboard component updating via WebSocket."""

    def __init__(self, url: str = "ws://localhost:6789", interval: int = 1000) -> None:
        self.url = url
        self.interval = interval
        self._controller = RealTimeWebSocketController()

    def layout(self) -> html.Div:
        return html.Div(
            [
                WebSocket(id="analytics-ws", url=self.url),
                dcc.Store(id="analytics-ws-store"),
                dcc.Interval(id="analytics-refresh", interval=self.interval),
                html.Div(id="analytics-summary"),
                html.Div(id="analytics-charts"),
            ]
        )

    def register_callbacks(self, manager: TrulyUnifiedCallbacks) -> None:
        @manager.callback(
            Output("analytics-ws-store", "data"),
            Input("analytics-ws", "message"),
            prevent_initial_call=True,
            callback_id="update_data",
            component_name="real_time_analytics",
        )
        def _update_data(message: dict | None) -> dict | None:
            data = self._controller.parse_message(message)
            if data is None:
                raise PreventUpdate
            return data

        @manager.callback(
            Output("analytics-summary", "children"),
            Output("analytics-charts", "children"),
            Input("analytics-refresh", "n_intervals"),
            State("analytics-ws-store", "data"),
            callback_id="update_view",
            component_name="real_time_analytics",
        )
        def _update_view(_n: int, data: dict | None) -> tuple[Any, Any]:
            if not data:
                raise PreventUpdate
            summary = self._controller.create_summary(data)
            charts = self._controller.create_charts(data)
            return summary, charts


__all__ = ["RealTimeAnalytics"]
