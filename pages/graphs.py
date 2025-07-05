#!/usr/bin/env python3
"""Graphs visualization page with placeholder content."""

from dash import html, dcc
import dash_bootstrap_components as dbc
from core.unicode_processor import sanitize_unicode_input
from services.analytics_summary import create_sample_data
from analytics.interactive_charts import create_charts_generator
from core.cache import cache


@cache.memoize()
def _generate_sample_figures():
    """Return a small set of sample figures using the analytics service."""
    try:
        df = create_sample_data(500)
        generator = create_charts_generator()
        charts = generator.generate_all_charts(df)

        return {
            "line": charts["temporal_analysis"]["time_series"],
            "bar": charts["door_analysis"]["door_usage"],
            "other": charts["risk_dashboard"]["risk_gauge"],
        }
    except Exception:
        # Fallback empty figures if chart generation fails
        import plotly.graph_objects as go

        empty = go.Figure()
        empty.update_layout(height=300, margin=dict(l=20, r=20, t=20, b=20))
        return {"line": empty, "bar": empty, "other": empty}


# Generate figures once at import time to avoid expensive recomputation
GRAPH_FIGURES = _generate_sample_figures()


def layout() -> dbc.Container:
    """Graphs page layout with sample charts."""

    figures = GRAPH_FIGURES

    tabs = dbc.Tabs(
        [
            dbc.Tab(
                dcc.Graph(figure=figures["line"]),
                label=sanitize_unicode_input("Line Charts"),
                tab_id="line",
            ),
            dbc.Tab(
                dcc.Graph(figure=figures["bar"]),
                label=sanitize_unicode_input("Bar Charts"),
                tab_id="bar",
            ),
            dbc.Tab(
                dcc.Graph(figure=figures["other"]),
                label=sanitize_unicode_input("Other"),
                tab_id="other",
            ),
        ],
        id="graphs-tabs",
        active_tab="line",
        className="mb-3",
    )

    return dbc.Container([tabs], fluid=True)


__all__ = ["layout"]
