#!/usr/bin/env python3
"""
Working upload page using existing sophisticated UnifiedUploadComponent
"""
from __future__ import annotations

import logging
from typing import Any

from dash import html, register_page as dash_register_page

# Import your existing sophisticated component
try:
    from components.upload import UnifiedUploadComponent
    COMPONENT_AVAILABLE = True
except ImportError as e:
    logging.warning(f"UnifiedUploadComponent not available: {e}")
    COMPONENT_AVAILABLE = False

logger = logging.getLogger(__name__)

def register_page() -> None:
    """Register the file upload page with Dash."""
    dash_register_page(__name__, path="/upload", name="Upload", aliases=["/file-upload"])

# Create the sophisticated component instance
_upload_component = UnifiedUploadComponent() if COMPONENT_AVAILABLE else None

def layout() -> html.Div:
    """Upload page using sophisticated UnifiedUploadComponent."""
    if _upload_component:
        return html.Div([
            html.H2("📁 File Upload", className="text-primary mb-4"),
            _upload_component.layout()
        ], className="page-container")
    else:
        import dash_bootstrap_components as dbc
        return dbc.Container([
            dbc.Alert("Upload component temporarily unavailable.", color="warning")
        ])

def safe_upload_layout():
    """Unicode-safe wrapper."""
    try:
        return layout()
    except Exception as e:
        logger.error(f"Upload layout failed: {e}")
        import dash_bootstrap_components as dbc
        return dbc.Container([
            dbc.Alert("Upload page temporarily unavailable.", color="warning")
        ])

def register_callbacks(manager: Any) -> None:
    """Register sophisticated upload callbacks."""
    if _upload_component and hasattr(_upload_component, 'register_callbacks'):
        try:
            _upload_component.register_callbacks(manager)
            logger.info("✅ Sophisticated upload callbacks registered")
        except Exception as e:
            logger.error(f"Failed to register upload callbacks: {e}")
    else:
        logger.info("No upload callbacks to register")

def check_upload_system_health():
    """Health check for upload system."""
    return {
        "status": "sophisticated" if COMPONENT_AVAILABLE else "unavailable",
        "component_available": COMPONENT_AVAILABLE
    }

__all__ = ["layout", "safe_upload_layout", "register_page", "register_callbacks", "check_upload_system_health"]
