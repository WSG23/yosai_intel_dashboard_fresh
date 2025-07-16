#!/usr/bin/env python3
"""
Simple stable analytics page - fixes navigation flash
Like Settings page - simple, stable, no complex components
"""
from __future__ import annotations

import logging
from typing import Any

import dash_bootstrap_components as dbc
from dash import html

from components.analytics.real_time_dashboard import RealTimeAnalytics
from components.layout_factory import card
from components.ui_component import UIComponent

logger = logging.getLogger(__name__)


class AnalyticsPage(UIComponent):
    """Simple analytics page component."""

    def __init__(self) -> None:
        super().__init__()
        self._realtime = RealTimeAnalytics()

    def layout(self) -> html.Div:  # type: ignore[override]
        return dbc.Container(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                card(
                                    "📊 Analytics Dashboard",
                                    [
                                        html.P(
                                            "Advanced analytics restored without"
                                            " navigation flash.",
                                            className="card-text",
                                        ),
                                        html.Hr(),
                                        html.I(
                                            className="fas fa-chart-line fa-3x mb-3",
                                            style={"color": "#007bff"},
                                            **{"aria-hidden": "true"},
                                        ),
                                        html.H6("✅ Navigation Flash: FIXED"),
                                        html.H6("🔧 Advanced Analytics: Coming Next"),
                                        html.P(
                                            "Page loads stable like Settings/Export",
                                            className="text-muted",
                                        ),
                                        html.Hr(),
                                        html.H6("📋 Planned Features:"),
                                        html.Ul(
                                            [
                                                html.H5(
                                                    "📊 Analytics Dashboard",
                                                    className="card-title",
                                                ),
                                                html.P(
                                                    (
                                                        "Advanced analytics restored "
                                                        "without navigation flash."
                                                    ),
                                                    className="card-text",
                                                ),
                                                html.Hr(),
                                                html.I(
                                                    className=(
                                                        "fas fa-chart-line fa-3x "
                                                        "mb-3 text-accent"
                                                    ),
                                                    **{"aria-hidden": "true"},
                                                ),
                                                html.H6("✅ Navigation Flash: FIXED"),
                                                html.H6(
                                                    "🔧 Advanced Analytics: Coming Next"
                                                ),
                                                html.P(
                                                    (
                                                        "Page loads stable like "
                                                        "Settings/Export"
                                                    ),
                                                    className="text-muted",
                                                ),
                                                html.Hr(),
                                                html.H6("📋 Planned Features:"),
                                                html.Ul(
                                                    [
                                                        html.Li(
                                                            "Data source selection"
                                                        ),
                                                        html.Li(
                                                            (
                                                                "Interactive charts "
                                                                "and graphs"
                                                            )
                                                        ),
                                                        html.Li(
                                                            "Device pattern analysis"
                                                        ),
                                                        html.Li("Anomaly detection"),
                                                        html.Li("Behavior analysis"),
                                                    ]
                                                ),
                                                html.Li("Device pattern analysis"),
                                                html.Li("Anomaly detection"),
                                                html.Li("Behavior analysis"),
                                            ]
                                        ),
                                    ],
                                    color="light",
                                )
                            ],
                            md=8,
                        )
                    ]
                ),
                dbc.Row([dbc.Col(self._realtime.layout())]),
            ],
            fluid=True,
        )

    def register_callbacks(
        self, manager: Any, controller: Any | None = None
    ) -> None:  # type: ignore[override]
        if manager:
            self._realtime.register_callbacks(manager)


_analytics_component = AnalyticsPage()


def load_page(**kwargs) -> AnalyticsPage:
    """Return a new :class:`AnalyticsPage` instance."""

    return AnalyticsPage(**kwargs)


def register_page() -> None:
    """Register the analytics page with Dash using current app context."""
    try:
        import dash

        if hasattr(dash, "_current_app") and dash._current_app is not None:
            dash.register_page(
                __name__,
                path="/analytics",
                name="Analytics",
                aliases=["/", "/dashboard"],
            )
        else:
            from dash import register_page as dash_register_page

            dash_register_page(
                __name__,
                path="/analytics",
                name="Analytics",
                aliases=["/", "/dashboard"],
            )
    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to register page {__name__}: {e}")


def layout() -> html.Div:
    """Compatibility wrapper returning the default component layout."""

    return _analytics_component.layout()


def register_callbacks(manager: Any) -> None:
    """Compatibility wrapper using the default component."""

    _analytics_component.register_callbacks(manager)


# For backward compatibility with app_factory
def deep_analytics_layout():
    """Compatibility function for app_factory."""
    return layout()


__all__ = [
    "AnalyticsPage",
    "load_page",
    "layout",
    "register_page",
    "register_callbacks",
    "deep_analytics_layout",
]


def __getattr__(name: str):
    if name.startswith(("create_", "get_")):

        def _stub(*args, **kwargs):
            return None

        return _stub
    raise AttributeError(f"module {__name__} has no attribute {name}")
