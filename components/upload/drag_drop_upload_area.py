#!/usr/bin/env python3
"""Accessible drag and drop upload area component."""
from __future__ import annotations

from dash import dcc, html


def DragDropUploadArea(upload_id: str = "drag-drop-upload") -> html.Div:
    """Return an accessible drag and drop upload area.

    The component exposes different state classes that can be toggled via
    JavaScript: ``--idle``, ``--hover``, ``--dragging``, ``--uploading``,
    ``--success`` and ``--error``.
    """

    status_id = f"{upload_id}-status"
    camera_id = f"{upload_id}-camera"
    preview_id = f"{upload_id}-previews"

    return html.Div(
        [
            dcc.Upload(
                id=upload_id,
                className="drag-drop-upload__input",
                multiple=True,
                children=html.Div(
                    [
                        html.Div(
                            [
                                html.I(
                                    className="fas fa-cloud-upload-alt fa-3x",
                                    **{"aria-hidden": "true"},
                                ),
                                html.Span("Upload icon", className="sr-only"),
                            ]
                        ),
                        html.P(
                            "Drag and drop files or press Enter to select",
                            id=f"{upload_id}-label",
                            className="mb-1",
                        ),
                        html.Button(
                            "Use Camera",
                            id=camera_id,
                            className="btn btn-secondary mt-2",
                            type="button",
                            **{"aria-label": "Use camera to capture"},
                        ),
                    ],
                    className="drag-drop-upload__inner",
                ),
            ),
            html.Ul(id=preview_id, className="drag-drop-upload__previews", role="list"),
            html.Div(
                id=status_id,
                className="drag-drop-upload__status",
                role="status",
                **{"aria-live": "polite"},
            ),
        ],
        id=f"{upload_id}-area",
        className="drag-drop-upload drag-drop-upload--idle",
        tabIndex=0,
        role="button",
        **{"aria-describedby": f"{upload_id}-label"},
    )


__all__ = ["DragDropUploadArea"]
