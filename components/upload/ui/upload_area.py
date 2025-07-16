"""Pure Dash UI component for drag-and-drop uploads."""

from __future__ import annotations

from typing import Callable

from dash import dcc, html


class UploadArea:
    """Drag and drop upload area without business logic."""

    def __init__(
        self,
        upload_handler: Callable | None = None,
        upload_id: str = "drag-drop-upload",
    ) -> None:
        self.upload_handler = upload_handler
        self.upload_id = upload_id
        self.status_id = f"{upload_id}-status"
        self.results_id = f"{upload_id}-results"

    def render(self) -> html.Div:
        return html.Div(
            [
                dcc.Upload(
                    id=self.upload_id,
                    children=self._render_upload_area(),
                    multiple=True,
                    **{"aria-label": "Upload files", "role": "button"},
                ),
                html.Div(id=self.status_id),
                html.Div(id=self.results_id),
            ]
        )

    def _render_upload_area(self) -> html.Div:
        return html.Div(
            [
                html.I(
                    className="fas fa-cloud-upload-alt fa-3x", **{"aria-hidden": "true"}
                ),
                html.H4("Drop files here or click to browse"),
            ]
        )

    def handle_file_drop(self, contents, filenames):
        if self.upload_handler:
            return self.upload_handler(contents, filenames)
        return "No handler configured"


__all__ = ["UploadArea"]
