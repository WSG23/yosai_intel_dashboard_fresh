# Fix the navbar import placement
with open('core/app_factory/__init__.py', 'r') as f:
    content = f.read()

# Move the import to the top of the file, not inside the function
content = content.replace(
    '''from dash import Dash, html, dcc
import dash_bootstrap_components as dbc''',
    '''from dash import Dash, html, dcc
import dash_bootstrap_components as dbc
from components.ui.navbar import create_navbar_layout'''
)

# Remove the duplicate import inside the function
content = content.replace(
    '''def create_main_layout():
    from components.ui.navbar import create_navbar_layout''',
    '''def create_main_layout():
    """Create minimal working layout with original navbar."""'''
)

with open('core/app_factory/__init__.py', 'w') as f:
    f.write(content)

print("✅ Fixed navbar import")
