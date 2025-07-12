from __future__ import annotations

import json
from typing import Any

from dash import dcc, html
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate
from dash_extensions import WebSocket

from components import create_analytics_charts, create_summary_cards


class RealTimeAnalytics:
    """Dashboard component updating via WebSocket."""

    def __init__(self, url: str = "ws://localhost:6789") -> None:
        self.url = url

    def layout(self) -> html.Div:
        return html.Div(
            [
                WebSocket(id="analytics-ws", url=self.url),
                dcc.Store(id="analytics-ws-store"),
                html.Div(id="analytics-summary"),
                html.Div(id="analytics-charts"),
            ]
        )

    def register_callbacks(self, app: Any) -> None:
        @app.callback(Output("analytics-ws-store", "data"), Input("analytics-ws", "message"))
        def _update_data(message: dict | None) -> dict | None:
            if not message:
                raise PreventUpdate
            try:
                return json.loads(message.get("data", "{}"))
            except Exception:
                raise PreventUpdate

        @app.callback(Output("analytics-summary", "children"), Input("analytics-ws-store", "data"))
        def _update_summary(data: dict | None) -> Any:
            if not data:
                raise PreventUpdate
            return create_summary_cards(data)

        @app.callback(Output("analytics-charts", "children"), Input("analytics-ws-store", "data"))
        def _update_charts(data: dict | None) -> Any:
            if not data:
                raise PreventUpdate
            return create_analytics_charts(data)


__all__ = ["RealTimeAnalytics"]
