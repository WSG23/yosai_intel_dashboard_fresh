#!/usr/bin/env python3
"""
Simple stable analytics page - fixes navigation flash
Like Settings page - simple, stable, no complex components
"""
from __future__ import annotations

import logging
from typing import Any

import dash_bootstrap_components as dbc
from dash import html, register_page as dash_register_page

logger = logging.getLogger(__name__)

def register_page() -> None:
    """Register the analytics page with Dash."""
    dash_register_page(__name__, path="/analytics", name="Analytics", aliases=["/", "/dashboard"])

def layout() -> html.Div:
    """Simple stable analytics layout - no Dropdown, no Loading, no flash."""
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("📊 Analytics Dashboard", className="card-title"),
                        html.P("Advanced analytics restored without navigation flash.", className="card-text"),
                        html.Hr(),
                        html.I(className="fas fa-chart-line fa-3x mb-3", style={"color": "#007bff"}),
                        html.H6("✅ Navigation Flash: FIXED"),
                        html.H6("🔧 Advanced Analytics: Coming Next"),
                        html.P("Page loads stable like Settings/Export", className="text-muted"),
                        html.Hr(),
                        html.H6("📋 Planned Features:"),
                        html.Ul([
                            html.Li("Data source selection"),
                            html.Li("Interactive charts and graphs"),
                            html.Li("Device pattern analysis"),
                            html.Li("Anomaly detection"),
                            html.Li("Behavior analysis")
                        ])
                    ])
                ], className="mb-4")
            ], md=8)
        ])
    ], fluid=True)

def register_callbacks(manager: Any) -> None:
    """No callbacks needed yet."""
    pass

# For backward compatibility with app_factory
def deep_analytics_layout():
    """Compatibility function for app_factory."""
    return layout()

__all__ = ["layout", "register_page", "register_callbacks", "deep_analytics_layout"]
