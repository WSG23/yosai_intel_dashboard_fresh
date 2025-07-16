#!/usr/bin/env python3
"""Graphs page - Full functionality with flash timing fix."""

import logging
import dash_bootstrap_components as dbc
from dash import dcc, html, register_page as dash_register_page

logger = logging.getLogger(__name__)


def _create_stable_chart():
    """Create chart with error handling."""
    try:
        import plotly.graph_objects as go

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(x=[1, 2, 3, 4], y=[10, 11, 12, 13], name="Sample Data")
        )
        fig.update_layout(
            title="Sample Chart",
            height=300,
            margin=dict(l=20, r=20, t=40, b=20),
            plot_bgcolor="white",
            paper_bgcolor="white",
        )
        return fig
    except ImportError:
        return {}


class GraphsPage:
    """Graphs page with pre-mount stability."""

    def layout(self):
        """Pre-rendered stable layout."""

        # Pre-create chart to prevent mounting flash
        chart_figure = _create_stable_chart()

        return dbc.Container(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.H2("📊 Graphs & Visualizations", className="mb-3"),
                                html.P(
                                    "Interactive data visualizations and charts",
                                    className="text-muted mb-4",
                                ),
                            ]
                        )
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Card(
                                    [
                                        dbc.CardHeader("Sample Chart"),
                                        dbc.CardBody(
                                            [
                                                dcc.Graph(
                                                    id="main-graph",
                                                    figure=chart_figure,
                                                    style={
                                                        "height": "300px",
                                                        "opacity": "1",
                                                        "visibility": "visible",
                                                    },
                                                )
                                            ]
                                        ),
                                    ],
                                    style={"opacity": "1", "visibility": "visible"},
                                )
                            ],
                            width=12,
                        )
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Card(
                                    [
                                        dbc.CardHeader("Chart Controls"),
                                        dbc.CardBody(
                                            [
                                                html.P(
                                                    "Chart customization controls coming soon.",
                                                    className="text-muted",
                                                )
                                            ]
                                        ),
                                    ]
                                )
                            ],
                            width=12,
                        )
                    ],
                    className="mt-4",
                ),
            ],
            fluid=True,
            className="py-4",
            style={"opacity": "1", "visibility": "visible"},
        )

    def register_callbacks(self, manager, controller=None):
        """Minimal callbacks."""
        pass


_graphs_component = GraphsPage()


def load_page(**kwargs):
    return GraphsPage(**kwargs)


def register_page(app=None):
    try:
        dash_register_page(__name__, path="/graphs", name="Graphs", app=app)
    except Exception as e:
        logger.warning(f"Failed to register page {__name__}: {e}")


def layout():
    return _graphs_component.layout()


def register_callbacks(manager):
    _graphs_component.register_callbacks(manager)


__all__ = ["GraphsPage", "load_page", "layout", "register_page"]
