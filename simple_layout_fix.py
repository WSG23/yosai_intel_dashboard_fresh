# Replace _create_main_layout with a working version
import re

with open('core/app_factory/__init__.py', 'r') as f:
    content = f.read()

# Replace the _create_main_layout function with a simple working version
new_layout = '''def _create_main_layout():
    """Simple working layout."""
    from dash import html, dcc
    from components.ui.navbar import create_navbar_layout
    
    return html.Div([
        dcc.Location(id="url", refresh=False),
        create_navbar_layout(),
        html.Div(id="page-content", children=[
            html.H1("🏯 Yōsai Dashboard"),
            html.P("Navigation should work now!")
        ], className="main-content p-4"),
        dcc.Store(id="global-store", data={}),
    ])'''

# Replace the existing _create_main_layout function
pattern = r'def _create_main_layout\(\).*?^def '
content = re.sub(pattern, new_layout + '\n\ndef ', content, flags=re.DOTALL | re.MULTILINE)

with open('core/app_factory/__init__.py', 'w') as f:
    f.write(content)
    
print("✅ Replaced with simple working layout")
