# Replace the basic navbar with the original navbar component
with open('core/app_factory/__init__.py', 'r') as f:
    content = f.read()

# Replace the layout function to use the original navbar
new_layout = '''def create_main_layout():
    """Create layout with original navbar component."""
    from components.ui.navbar import create_navbar_layout
    
    return html.Div([
        dcc.Location(id="url", refresh=False),
        create_navbar_layout(),
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

# Replace the layout function
import re
content = re.sub(r'def create_main_layout\(\):.*?(?=def create_app)', new_layout, content, flags=re.DOTALL)

with open('core/app_factory/__init__.py', 'w') as f:
    f.write(content)

print("✅ Restored original navbar component")
