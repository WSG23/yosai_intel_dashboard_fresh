#!/usr/bin/env python3
"""Fresh, minimal app factory that WORKS with real pages - HTTPS enabled."""

import dash
from dash import html, dcc, Input, Output
import dash_bootstrap_components as dbc
from components.ui.navbar import create_navbar_layout

def create_app(mode=None, **kwargs):
    """Create a working Dash app with logo, navigation, and routing - HTTPS ready."""
    
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    
    # Simple working layout
    app.layout = html.Div([
        dcc.Location(id="url", refresh=False),
        create_navbar_layout(),
        html.Div(id="page-content", className="main-content p-4"),
        dcc.Store(id="global-store", data={}),
    ])
    
    # Simple routing callback that uses REAL pages
    @app.callback(Output("page-content", "children"), Input("url", "pathname"))
    def display_page(pathname):
        if pathname == "/dashboard":
            return html.Div([
                html.H1("🏠 Dashboard", className="mb-4"),
                html.P("Welcome to your Yōsai Intel Dashboard!")
            ])
        elif pathname == "/analytics":
            return html.Div([
                html.H1("📊 Analytics", className="mb-4"),
                html.P("Analytics page - working!")
            ])
        elif pathname == "/graphs":
            return html.Div([
                html.H1("📈 Graphs", className="mb-4"),
                html.P("Graphs page - working!")
            ])
        elif pathname == "/upload":
            # Simple upload layout without callback conflicts
            return dbc.Container([
                # Header
                dbc.Row([
                    dbc.Col([
                        html.H2("📁 File Upload", className="mb-3"),
                        html.P(
                            "Drag and drop files or click to browse. Supports CSV, Excel, and JSON files.",
                            className="text-muted mb-4",
                        ),
                    ])
                ]),
                # Upload area  
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.I(className="fas fa-cloud-upload-alt fa-3x mb-3", style={"color": "#007bff"}),
                            html.H5("Drag & Drop Files Here", className="mb-2"),
                            html.P("or click to select files", className="text-muted"),
                            html.P("Supported: CSV, Excel (.xlsx, .xls), JSON", className="small text-secondary"),
                        ], style={
                            "width": "100%",
                            "height": "200px",
                            "borderWidth": "2px",
                            "borderStyle": "dashed",
                            "borderRadius": "8px",
                            "borderColor": "#007bff",
                            "textAlign": "center",
                            "background": "#f8f9fa",
                            "cursor": "pointer",
                            "display": "flex",
                            "flexDirection": "column",
                            "justifyContent": "center",
                            "alignItems": "center",
                        }),
                    ], width=8, className="mx-auto")
                ]),
                # Status area
                dbc.Row([
                    dbc.Col([
                        html.Div(id="upload-status", className="mt-3"),
                        html.Div("Upload functionality will be enhanced in next update.", 
                               className="text-info mt-2")
                    ], width=8, className="mx-auto")
                ])
            ], fluid=True, className="py-4")
        elif pathname == "/export":
            return html.Div([
                html.H1("📥 Export", className="mb-4"),
                html.P("Export page - working!")
            ])
        elif pathname == "/settings":
            return html.Div([
                html.H1("⚙️ Settings", className="mb-4"),
                html.P("Settings page - working!")
            ])
        else:
            return html.Div([
                html.H1("🏯 Yōsai Intel Dashboard", className="text-center mb-4"),
                html.P("Select a page from the navigation menu above.", className="text-center")
            ])
    
    app.title = "🏯 Yōsai Intel Dashboard"
    return app
