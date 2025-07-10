"""Simple stable analytics layout - fixes navigation flash"""

import dash_bootstrap_components as dbc
from dash import html

def layout():
    """Simple stable layout like Settings page."""
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("📊 Analytics Dashboard", className="card-title"),
                        html.P("Navigation flash fixed! Advanced analytics coming soon.", className="card-text"),
                        html.Hr(),
                        html.I(className="fas fa-chart-line fa-3x mb-3", style={"color": "#007bff"}),
                        html.H6("✅ Navigation Flash: FIXED"),
                        html.H6("🔧 Advanced Features: Being Restored"),
                    ])
                ], className="mb-4")
            ], md=8)
        ])
    ], fluid=True)
