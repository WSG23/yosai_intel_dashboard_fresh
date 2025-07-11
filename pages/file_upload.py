from dash import html
import dash_bootstrap_components as dbc

# Import your existing upload component function
try:
    from components import create_upload_card  # Use existing function
    HAS_UPLOAD_COMPONENT = True
except ImportError:
    HAS_UPLOAD_COMPONENT = False

def layout():
    if HAS_UPLOAD_COMPONENT:
        return dbc.Container([
            html.H2("File Upload"),
            create_upload_card()  # Use existing upload component
        ])
    else:
        return dbc.Container([
            html.H2("File Upload"),
            html.P("Upload component not available")
        ])

def safe_upload_layout():
    return layout()

def register_callbacks(manager):
    pass

def register_page():
    from dash import register_page as dash_register_page
    dash_register_page(__name__, path="/upload", name="Upload")

__all__ = ["layout", "safe_upload_layout", "register_page", "register_callbacks"]
