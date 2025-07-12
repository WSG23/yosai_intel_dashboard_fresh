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

from dash import dcc, html, register_page as dash_register_page
from security.unicode_security_processor import sanitize_unicode_input

# ✅ FIXED: Initialize cache as None, set up lazily
cache = None

def register_page() -> None:
    """Register the graphs page with Dash."""
    dash_register_page(__name__, path="/graphs", name="Graphs")

def _setup_cache_if_needed():
    """Setup cache if app context is available."""
    global cache
    if cache is None:
        try:
            from dash import current_app
            if current_app:
                from flask_caching import Cache
                cache = Cache(current_app.server, config={'CACHE_TYPE': 'simple'})
        except:
            cache = None  # Fallback if no app context

def _create_figures() -> Dict[str, Any]:
    """Create sample figures for the graphs page."""
    # Try to use cache if available
    _setup_cache_if_needed()
    
    if not (pd and px):
        return {k: (go.Figure() if go else None) for k in ("line", "bar", "other")}

    try:
        df = pd.DataFrame(
            {
                "date": pd.date_range(end=pd.Timestamp.today(), periods=30),
                "door": [f"Door {i%3+1}" for i in range(30)],
                "count": [int(i * 1.5) % 50 + 10 for i in range(30)],
            }
        )
        line_fig = px.line(df, x="date", y="count", title="Access Count Over Time")
        bar_fig = px.bar(df, x="door", y="count", title="Access Count by Door")
        scatter_fig = px.scatter(
            df, x="date", y="count", color="door", title="Door Activity"
        )
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
    
    # ✅ FIXED: Setup cache when layout is called
    _setup_cache_if_needed()
    
    if _FIGURES is None:
        _FIGURES = _create_figures()

    return dbc.Container(
        [
            html.H2("📊 Graphs & Visualizations"),
            html.P("Interactive data visualizations and charts"),
            html.Hr(),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Line Chart"),
                        dbc.CardBody([
                            dcc.Graph(figure=_FIGURES.get("line", {}))
                        ])
                    ])
                ], md=6),
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Bar Chart"), 
                        dbc.CardBody([
                            dcc.Graph(figure=_FIGURES.get("bar", {}))
                        ])
                    ])
                ], md=6),
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Scatter Plot"),
                        dbc.CardBody([
                            dcc.Graph(figure=_FIGURES.get("other", {}))
                        ])
                    ])
                ], md=12),
            ])
        ],
        fluid=True
    )
