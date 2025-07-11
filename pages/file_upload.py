"""File upload page wired to the unified upload component."""

from dash import html
import dash_bootstrap_components as dbc

from components.upload import UnifiedUploadComponent
from services.upload_data_service import get_uploaded_filenames as _get_uploaded_filenames


# Instantiate the shared upload component once
_upload_component = UnifiedUploadComponent()


def layout() -> html.Div:
    """Render the upload page using the unified component."""
    return _upload_component.layout()


def safe_upload_layout() -> html.Div:
    """Compatibility wrapper used by legacy routing."""
    return layout()


def register_callbacks(manager) -> None:
    """Delegate callback registration to the component."""
    _upload_component.register_callbacks(manager)


# Dash tests expect this alias
register_upload_callbacks = register_callbacks


def get_uploaded_filenames():
    """Expose helper for tests to query uploaded files."""
    return _get_uploaded_filenames()

def register_page():
    from dash import register_page as dash_register_page
    dash_register_page(__name__, path="/upload", name="Upload")


__all__ = [
    "layout",
    "safe_upload_layout",
    "register_page",
    "register_callbacks",
    "register_upload_callbacks",
    "get_uploaded_filenames",
    "_upload_component",
]
