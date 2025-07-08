"""Unified upload component with proper DI integration."""
from __future__ import annotations

import dash_bootstrap_components as dbc
from dash import dcc, html
from typing import Protocol, runtime_checkable

from core.unicode_processor import safe_format_text
from services.interfaces import UploadValidatorProtocol


@runtime_checkable
class UploadHandlerProtocol(Protocol):
    """Protocol for upload handling with Unicode safety."""

    def handle_upload(self, contents: list, filenames: list) -> dict:
        """Handle file upload with Unicode surrogate character safety."""
        ...

    def validate_upload(self, filename: str, content: bytes) -> bool:
        """Validate upload content."""
        ...


class UnifiedUploadComponent:
    """Consolidated upload component with DI and Unicode safety."""

    def __init__(
        self,
        container,
        upload_id: str = "unified-upload",
        *,
        max_size: int | None = None,
    ) -> None:
        self.upload_id = upload_id
        self.max_size = max_size
        self.container = container
        self._validator = None
        self._handler = None

    @property
    def validator(self) -> UploadValidatorProtocol:
        """Lazy-loaded validator from DI container."""
        if self._validator is None:
            self._validator = self.container.get("upload_validator")
        return self._validator

    @property
    def handler(self) -> UploadHandlerProtocol:
        """Lazy-loaded handler from DI container."""
        if self._handler is None:
            self._handler = self.container.get("upload_processor")
        return self._handler

    def render(self) -> dbc.Card:
        """Render the unified upload component."""
        return dbc.Card([
            dbc.CardHeader([
                html.H5(safe_format_text("Upload Data Files"), className="mb-0")
            ]),
            dbc.CardBody([
                self._render_upload_area(),
                self._render_progress_area(),
                self._render_results_area(),
            ])
        ])

    def _render_upload_area(self) -> dcc.Upload:
        """Render the drag-drop upload area."""
        return dcc.Upload(
            id=self.upload_id,
            max_size=self.max_size,
            multiple=True,
            children=html.Div([
                html.Div([
                    html.I(
                        className="fas fa-cloud-upload-alt fa-4x mb-3 text-primary",
                        **{"aria-hidden": "true"},
                    ),
                    html.Span("Upload icon", className="sr-only"),
                ]),
                html.H5(
                    safe_format_text("Drag and Drop or Click to Upload"),
                    className="text-primary"
                ),
                html.P(
                    safe_format_text("Supports CSV, Excel (.xlsx, .xls), and JSON files"),
                    className="text-muted mb-0",
                ),
            ]),
            className="upload-dropzone",
            role="button",
            tabIndex=0,
            **{"aria-label": "File upload area"},
        )

    def _render_progress_area(self) -> html.Div:
        """Render progress tracking area."""
        return html.Div([
            dbc.Progress(
                id=f"{self.upload_id}-progress",
                value=0,
                label="0%",
                striped=True,
                animated=True,
                className="mb-2"
            ),
            html.Ul(
                id=f"{self.upload_id}-progress-list",
                className="list-unstyled"
            ),
        ])

    def _render_results_area(self) -> html.Div:
        """Render upload results area."""
        return html.Div([
            html.Div(id=f"{self.upload_id}-status"),
            html.Div(id=f"{self.upload_id}-results"),
            dcc.Store(id=f"{self.upload_id}-data"),
            dcc.Store(id=f"{self.upload_id}-info"),
        ])


__all__ = ["UnifiedUploadComponent", "UploadHandlerProtocol"]
