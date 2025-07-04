#!/usr/bin/env python3
"""Accessible drag and drop upload area component."""
from __future__ import annotations

import dash_bootstrap_components as dbc
from dash import dcc, html


def DragDropUploadArea(upload_id: str = "drag-drop-upload") -> html.Div:
    """Return an accessible drag and drop upload area.

    The component exposes different state classes that can be toggled via
    JavaScript: ``--idle``, ``--hover``, ``--dragging``, ``--uploading``,
    ``--success`` and ``--error``.
    """

    status_id = f"{upload_id}-status"
    camera_id = f"{upload_id}-camera"

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
                        dbc.Button(
                            "Use Camera",
                            id=camera_id,
                            color="secondary",
                            size="sm",
                            className="mt-2",
                            **{"aria-label": "Use camera to capture"},
                        ),
                    ],
                    className="drag-drop-upload__inner",
                ),
            ),
            html.Div(id=status_id, className="drag-drop-upload__status", role="status"),
        ],
        id=f"{upload_id}-area",
        className="drag-drop-upload drag-drop-upload--idle",
        tabIndex=0,
        role="button",
        **{"aria-describedby": f"{upload_id}-label"},
    )


__all__ = ["DragDropUploadArea"]
