"""Device verification component - follows exact same pattern as column_verification.py"""

import pandas as pd
from dash import html, dcc
from dash.dependencies import Input, Output, State, ALL, MATCH
from core.unified_callback_coordinator import UnifiedCallbackCoordinator
from analytics.controllers import UnifiedAnalyticsController
import logging

logger = logging.getLogger(__name__)
import dash
import dash_bootstrap_components as dbc
from typing import Dict, List, Any, Union
import logging
from datetime import datetime
from components.simple_device_mapping import special_areas_options
from services.ai_mapping_store import ai_mapping_store

logger = logging.getLogger(__name__)


def create_device_verification_modal(
    device_mappings: Dict[str, Dict], session_id: str
) -> Union[dbc.Modal, html.Div]:
    """Create device verification modal - same pattern as column verification"""

    if not device_mappings:
        return html.Div()

    # Create table rows for each device
    table_rows = []
    for i, (device_name, attributes) in enumerate(device_mappings.items()):
        confidence = attributes.get("confidence", 0.0)

        table_rows.append(
            html.Tr(
                [
                    # Device name and confidence
                    html.Td(
                        [
                            html.Strong(device_name),
                            html.Br(),
                            html.Small(
                                f"AI Confidence: {confidence:.0%}",
                                className=(
                                    "text-muted" if confidence < 0.5 else "text-success"
                                ),
                            ),
                        ],
                        className="device-verification__col--name",
                    ),
                    # Floor number
                    html.Td(
                        [
                            dbc.Input(
                                id={"type": "device-floor", "index": i},
                                type="number",
                                min=0,
                                max=50,
                                value=attributes.get("floor_number"),
                                placeholder="Floor #",
                                size="sm",
                            )
                        ],
                        className="device-verification__col--floor",
                    ),
                    # Entry/Exit checkboxes
                    html.Td(
                        [
                            dbc.Checklist(
                                id={"type": "device-access", "index": i},
                                options=[
                                    {"label": "Entry", "value": "is_entry"},
                                    {"label": "Exit", "value": "is_exit"},
                                ],
                                value=[
                                    key
                                    for key in ["is_entry", "is_exit"]
                                    if attributes.get(key, attributes.get(key.replace("is_", "")))
                                ],
                                inline=True,
                            )
                        ],
                        className="device-verification__col--access",
                    ),
                    # Special areas
                    html.Td(
                        [
                            dbc.Checklist(
                                id={"type": "device-special", "index": i},
                                options=special_areas_options,
                                value=[
                                    key
                                    for key in [
                                        "is_elevator",
                                        "is_stairwell",
                                        "is_fire_escape",
                                        "is_restricted",
                                    ]
                                    if attributes.get(key, attributes.get(key.replace("is_", "")))
                                ],
                                inline=False,
                                className="small",
                            )
                        ],
                        className="device-verification__col--special",
                    ),
                    # Security level
                    html.Td(
                        [
                            dbc.Input(
                                id={"type": "device-security", "index": i},
                                type="number",
                                min=0,
                                max=10,
                                value=attributes.get("security_level", 1),
                                placeholder="0-10",
                                size="sm",
                            )
                        ],
                        className="device-verification__col--security",
                    ),
                    # Manually edited flag (hidden input)
                    html.Td(
                        [
                            dcc.Store(
                                id={"type": "device-name", "index": i}, data=device_name
                            ),
                            dcc.Store(
                                id={"type": "device-edited", "index": i}, data=False
                            ),
                        ],
                        className="hidden",
                        style={"width": "0%"},

                    ),
                ]
            )
        )

    modal_body = html.Div(
        [
            html.H5(f"Device Classification - {len(device_mappings)} devices found"),
            dbc.Alert(
                [
                    "AI has analyzed your devices and made suggestions. ",
                    "Review and correct any mistakes to help the AI learn.",
                ],
                color="info",
                className="mb-3",
            ),
            dbc.Table(
                [
                    html.Thead(
                        [
                            html.Tr(
                                [
                                    html.Th("Device Name", className="device-verification__col--name"),
                                    html.Th("Floor", className="device-verification__col--floor"),
                                    html.Th("Access Type", className="device-verification__col--access"),
                                    html.Th("Special Areas", className="device-verification__col--special"),
                                    html.Th("Security (0-10)", className="device-verification__col--security"),
                                ]
                            )
                        ]
                    ),
                    html.Tbody(table_rows),
                ],
                striped=True,
                hover=True,
                size="sm",
            ),
            dbc.Card(
                [
                    dbc.CardHeader(html.H6("Security Level Guide", className="mb-0")),
                    dbc.CardBody(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            dbc.Badge("0-2", color="success"),
                                            " Public areas (lobby, restrooms)",
                                        ],
                                        width=6,
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.Badge("3-5", color="warning"),
                                            " General office areas",
                                        ],
                                        width=6,
                                    ),
                                ]
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            dbc.Badge("6-8", color="danger"),
                                            " Restricted areas (server rooms)",
                                        ],
                                        width=6,
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.Badge("9-10", color="dark"),
                                            " High security (executive, finance)",
                                        ],
                                        width=6,
                                    ),
                                ],
                                className="mt-2",
                            ),
                        ]
                    ),
                ],
                className="mt-3",
            ),
        ]
    )

    return dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("AI Device Classification Verification")),
            dbc.ModalBody(modal_body, id="device-modal-body"),
            dbc.ModalFooter(
                [
                    dbc.Button(
                        "Cancel",
                        id="device-verify-cancel",
                        color="secondary",
                        className="me-2",
                    ),
                    dbc.Button(
                        "Confirm & Train AI",
                        id="device-verify-confirm",
                        color="success",
                    ),
                ]
            ),
        ],
        id="device-verification-modal",
        size="xl",
        is_open=False,
        scrollable=True,
    )


def mark_device_as_edited(floor, access, special, security):
    """Mark device as manually edited when user makes changes"""
    return True  # Simplified - any change marks as edited


def register_callbacks(
    manager: UnifiedCallbackCoordinator,
    controller: UnifiedAnalyticsController | None = None,
) -> None:
    """Register component callbacks using the provided coordinator."""

    manager.register_callback(
        Output({"type": "device-edited", "index": MATCH}, "data"),
        [
            Input({"type": "device-floor", "index": MATCH}, "value"),
            Input({"type": "device-access", "index": MATCH}, "value"),
            Input({"type": "device-special", "index": MATCH}, "value"),
            Input({"type": "device-security", "index": MATCH}, "value"),
        ],
        prevent_initial_call=True,
        callback_id="mark_device_as_edited",
        component_name="device_verification",
    )(mark_device_as_edited)

    if controller is not None:
        controller.register_callback(
            "on_analysis_error",
            lambda aid, err: logger.error("Device verification error: %s", err),
        )


__all__ = ["create_device_verification_modal", "register_callbacks"]
