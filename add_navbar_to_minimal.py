# Add proper navbar to minimal app factory
with open('core/app_factory/__init__.py', 'r') as f:
    content = f.read()

# Replace the minimal nav with full navbar
new_layout = '''def create_main_layout():
    """Create minimal working layout with full navbar."""
    return html.Div([
        dcc.Location(id="url", refresh=False),
        
        # Full Navbar with navigation
        html.Nav([
            dbc.Container([
                dbc.Row([
                    dbc.Col([
                        html.A([
                            html.Img(src="/assets/logo.png", height="30", className="me-2"),
                            html.Span("🏯 Yōsai Intel Dashboard", className="navbar-brand")
                        ], href="/dashboard", className="navbar-brand text-white text-decoration-none")
                    ], width="auto"),
                    dbc.Col([
                        html.Ul([
                            html.Li([
                                html.A("Dashboard", href="/dashboard", className="nav-link text-white")
                            ], className="nav-item"),
                            html.Li([
                                html.A("Analytics", href="/analytics", className="nav-link text-white")
                            ], className="nav-item"),
                            html.Li([
                                html.A("Upload", href="/upload", className="nav-link text-white")
                            ], className="nav-item"),
                            html.Li([
                                html.A("Graphs", href="/graphs", className="nav-link text-white")
                            ], className="nav-item"),
                            html.Li([
                                html.A("Export", href="/export", className="nav-link text-white")
                            ], className="nav-item"),
                            html.Li([
                                html.A("Settings", href="/settings", className="nav-link text-white")
                            ], className="nav-item"),
                        ], className="nav nav-pills d-flex", style={"list-style": "none", "margin": "0", "padding": "0"})
                    ], className="d-flex justify-content-center")
                ], className="w-100 d-flex justify-content-between align-items-center")
            ], fluid=True)
        ], className="navbar", style={"background": "#1f2937", "padding": "10px 0", "margin-bottom": "20px"}),
        
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
        dcc.Store(id="global-store", data={}),
    ])'''

# Replace the old layout function
import re
content = re.sub(r'def create_main_layout\(\):.*?(?=def create_app)', new_layout, content, flags=re.DOTALL)

with open('core/app_factory/__init__.py', 'w') as f:
    f.write(content)

print("✅ Added full navbar to minimal app")
