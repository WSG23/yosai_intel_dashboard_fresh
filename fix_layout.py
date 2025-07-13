#!/usr/bin/env python3
"""Quick fix to replace the broken layout function."""

def create_working_layout():
    """Create a minimal working layout with dcc.Location and manual routing."""
    from dash import dcc, html
    import dash_bootstrap_components as dbc
    
    return html.Div([
        # URL component - this is critical for routing
        dcc.Location(id="url", refresh=False),
        
        # Simple navbar
        html.Nav([
            html.H3("🏯 Yōsai Dashboard", style={"color": "white", "padding": "15px", "margin": "0"}),
        ], style={"background": "#1f2937", "margin-bottom": "20px"}),
        
        # Content area for manual routing
        html.Div(
            id="page-content", 
            children=[
                dbc.Container([
                    html.H1("🚀 Loading Dashboard..."),
                    html.P("Manual routing should populate this area momentarily."),
                ])
            ],
            style={"padding": "20px"}
        ),
        
        # Basic stores
        dcc.Store(id="global-store", data={}),
    ])

if __name__ == "__main__":
    # Test the layout
    layout = create_working_layout()
    print(f"✅ Layout created: {type(layout)}")
    print(f"✅ Contains Location: {'Location' in str(layout)}")
    print(f"✅ Contains page-content: {'page-content' in str(layout)}")
