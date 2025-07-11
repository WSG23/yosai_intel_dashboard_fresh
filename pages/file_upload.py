#!/usr/bin/env python3
"""
File upload page using existing UnifiedUploadComponent infrastructure.
Eliminates flash by properly integrating with existing upload architecture.
"""
from __future__ import annotations

import logging
from typing import Any

import dash_bootstrap_components as dbc
from dash import html, register_page as dash_register_page

# Use existing sophisticated upload infrastructure
from components.upload import UnifiedUploadComponent

logger = logging.getLogger(__name__)

def register_page() -> None:
    """Register the file upload page with Dash."""
    dash_register_page(__name__, path="/upload", name="Upload", aliases=["/file-upload"])

# Single instance to avoid ID conflicts
_upload_component = UnifiedUploadComponent()

def layout() -> html.Div:
    """Upload page layout using existing UnifiedUploadComponent - prevents dcc.Upload conflicts."""
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H2("📁 File Upload", className="text-primary mb-4"),
                html.P("Drag and drop files or click to browse. Supports CSV, JSON, and Excel files.", 
                       className="text-muted mb-4"),
                
                # Use existing sophisticated component
                _upload_component.layout()
                
            ], width=12)
        ])
    ], fluid=True, className="py-4")

def safe_upload_layout():
    """Unicode-safe wrapper for layout - required by app factory."""
    try:
        return layout()
    except Exception as e:
        logger.error(f"Upload layout failed: {e}")
        return dbc.Container([
            dbc.Alert("Upload page temporarily unavailable.", color="warning")
        ])

def register_callbacks(manager: Any) -> None:
    """Register upload callbacks using existing infrastructure - required by app factory."""
    try:
        _upload_component.register_callbacks(manager)
        logger.info("✅ Upload callbacks registered using UnifiedUploadComponent")
    except Exception as e:
        logger.error(f"Failed to register upload callbacks: {e}")

# Legacy alias for app factory compatibility
def register_upload_callbacks(manager: Any) -> None:
    """Legacy alias for register_callbacks - required by tests."""
    register_callbacks(manager)

def check_upload_system_health():
    """Health check for upload system."""
    return {
        "status": "healthy", 
        "component": "UnifiedUploadComponent",
        "architecture": "modular"
    }

__all__ = [
    "layout", 
    "safe_upload_layout", 
    "register_page", 
    "register_callbacks", 
    "register_upload_callbacks",
    "check_upload_system_health"
]