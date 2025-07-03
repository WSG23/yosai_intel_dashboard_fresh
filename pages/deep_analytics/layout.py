"""Layout components for the deep analytics page."""

import logging
from dash import html, dcc
import dash_bootstrap_components as dbc
from .analysis import (
    get_data_source_options_safe,
    get_latest_uploaded_source_value,
)

logger = logging.getLogger(__name__)


def layout():
    """Fixed layout without problematic Unicode characters"""
    try:
        # Header section - using safe ASCII characters
        header = dbc.Row([
            dbc.Col([
                html.H1("Deep Analytics", className="text-primary"),
                html.P(
                    "Advanced data analysis with AI-powered column mapping suggestions",
                    className="lead text-muted"
                ),
                dbc.Alert(
                    "UI components loaded successfully",
                    color="success",
                    dismissable=True,
                    id="status-alert"
                )
            ])
        ], className="mb-4")

        # Configuration section
        config_card = dbc.Card([
            dbc.CardHeader([html.H5("Analysis Configuration")]),
            dbc.CardBody([
                dbc.Row([
                    # Data source column
                    dbc.Col([
                        html.Label(
                            "Data Source",
                            htmlFor="analytics-data-source",
                            className="fw-bold"
                        ),
                        dcc.Dropdown(
                            id="analytics-data-source",
                            options=get_data_source_options_safe(),
                            placeholder="Select data source...",
                            value=get_latest_uploaded_source_value()
                        )
                    ], width=6),
                    
                    # Analysis buttons column  
                    dbc.Col([
                        html.Label(
                            "Analysis Type",
                            htmlFor="security-btn",
                            className="fw-bold mb-3"
                        ),
                        dbc.Row([
                            dbc.Col([
                                dbc.Button(
                                    "Security Analysis",
                                    id="security-btn",
                                    color="danger",
                                    outline=True,
                                    size="sm",
                                    className="w-100 mb-2"
                                )
                            ], width=6),
                            dbc.Col([
                                dbc.Button(
                                    "Trends Analysis", 
                                    id="trends-btn",
                                    color="info",
                                    outline=True,
                                    size="sm", 
                                    className="w-100 mb-2"
                                )
                            ], width=6),
                            dbc.Col([
                                dbc.Button(
                                    "Behavior Analysis",
                                    id="behavior-btn", 
                                    color="warning",
                                    outline=True,
                                    size="sm",
                                    className="w-100 mb-2"
                                )
                            ], width=6),
                            dbc.Col([
                                dbc.Button(
                                    "Anomaly Detection",
                                    id="anomaly-btn",
                                    color="dark", 
                                    outline=True,
                                    size="sm",
                                    className="w-100 mb-2"
                                )
                            ], width=6),
                            dbc.Col([
                                dbc.Button(
                                    "AI Suggestions",
                                    id="suggests-btn",
                                    color="success",
                                    outline=True, 
                                    size="sm",
                                    className="w-100 mb-2"
                                )
                            ], width=6),
                            dbc.Col([
                                dbc.Button(
                                    "Data Quality",
                                    id="quality-btn",
                                    color="secondary",
                                    outline=True,
                                    size="sm",
                                    className="w-100 mb-2"
                                )
                            ], width=6),
                            dbc.Col([
                                dbc.Button(
                                    "Unique Patterns",
                                    id="unique-patterns-btn",
                                    color="primary",
                                    outline=True,
                                    size="sm",
                                    className="w-100 mb-2"
                                )
                            ], width=6)
                        ])
                    ], width=6)
                ], className="mb-3"),
                html.Hr(),
                dbc.ButtonGroup([
                    dbc.Button(
                        "Refresh Data Sources",
                        id="refresh-sources-btn",
                        color="outline-secondary", 
                        size="lg"
                    )
                ])
            ])
        ], className="mb-4")

        # Results display area
        results_area = html.Div(
            id="analytics-display-area",
            children=[
                dbc.Alert([
                    html.H6("Get Started"),
                    html.P("1. Select a data source from the dropdown"),
                    html.P("2. Click any analysis button to run immediately"),
                    html.P("Each button runs its analysis type automatically")
                ], color="info")
            ]
        )

        # Hidden stores
        stores = [
            dcc.Store(id="service-health-store", data={}),
            html.Div(id="hidden-trigger", className="hidden")
        ]

        return dbc.Container([header, config_card, results_area] + stores, fluid=True)

    except Exception as e:
        logger.error(f"Layout creation error: {e}")
        return dbc.Container([
            dbc.Alert([
                html.H4("Page Loading Error"),
                html.P(f"Error: {str(e)}"),
                html.P("Please check imports and dependencies")
            ], color="danger")
        ], fluid=True)

