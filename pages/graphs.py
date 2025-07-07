"""Interactive graphs page for the dashboard."""

from __future__ import annotations

import logging
from typing import Any, Dict

import dash_bootstrap_components as dbc

try:
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
except Exception as e:  # pragma: no cover - optional plotting deps
    logging.getLogger(__name__).warning("Plotting libraries unavailable: %s", e)
    pd = None
    px = None
    go = None

from core.cache import cache
from dash import dcc, html
from security.unicode_security_processor import sanitize_unicode_input


@cache.memoize()
def _create_figures() -> Dict[str, Any]:
    """Create sample figures for the graphs page."""
    if not (pd and px):
        return {k: (go.Figure() if go else None) for k in ("line", "bar", "other")}

    try:
        df = pd.DataFrame({
            "date": pd.date_range(end=pd.Timestamp.today(), periods=30),
            "door": [f"Door {i%3+1}" for i in range(30)],
            "count": [int(i * 1.5) % 50 + 10 for i in range(30)],
        })
        line_fig = px.line(df, x="date", y="count", title="Access Count Over Time")
        bar_fig = px.bar(df, x="door", y="count", title="Access Count by Door")
        scatter_fig = px.scatter(df, x="date", y="count", color="door", title="Door Activity")
        for fig in (line_fig, bar_fig, scatter_fig):
            fig.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20))
        return {"line": line_fig, "bar": bar_fig, "other": scatter_fig}
    except Exception as exc:  # pragma: no cover - defensive fallback
        logging.getLogger(__name__).exception("Figure generation failed: %s", exc)
        empty = go.Figure() if go else None
        return {"line": empty, "bar": empty, "other": empty}


_FIGURES: Dict[str, Any] | None = None


def layout() -> dbc.Container:
    """Return the graphs page layout."""
    global _FIGURES
    if _FIGURES is None:
        _FIGURES = _create_figures()

    tabs = dbc.Tabs(
        [
            dbc.Tab(dcc.Graph(figure=_FIGURES.get("line") if _FIGURES else None), label=sanitize_unicode_input("Line"), tab_id="line"),
            dbc.Tab(dcc.Graph(figure=_FIGURES.get("bar") if _FIGURES else None), label=sanitize_unicode_input("Bar"), tab_id="bar"),
            dbc.Tab(dcc.Graph(figure=_FIGURES.get("other") if _FIGURES else None), label=sanitize_unicode_input("Other"), tab_id="other"),
        ],
        id="graphs-tabs",
        active_tab="line",
        className="mb-3",
    )
    return dbc.Container([tabs], fluid=True)


__all__ = ["layout"]
