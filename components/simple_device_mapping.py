"""Simple manual device mapping component"""

from typing import TYPE_CHECKING

import dash
from dash import html
from dash._callback_context import callback_context

if TYPE_CHECKING:
    from core.truly_unified_callbacks import TrulyUnifiedCallbacks

import logging

from analytics.controllers.unified_controller import UnifiedAnalyticsController
from core.error_handling import handle_errors

logger = logging.getLogger(__name__)
from typing import Any, Dict, List

import dash_bootstrap_components as dbc
import pandas as pd
from dash.dependencies import ALL, Input, Output, State

from services.ai_mapping_store import ai_mapping_store
# Import helper to access the learning service via the DI container
from services.interfaces import (
    DoorMappingServiceProtocol,
    get_door_mapping_service,
    get_device_learning_service,
)

# Options for special device areas shared with verification component
special_areas_options = [
    {"label": "Elevator", "value": "is_elevator"},
    {"label": "Stairwell", "value": "is_stairwell"},
    {"label": "Fire Exit", "value": "is_fire_escape"},
    {"label": "Restricted", "value": "is_restricted"},
]


def apply_learned_device_mappings(
    df: pd.DataFrame,
    filename: str,
    door_service: DoorMappingServiceProtocol | None = None,
) -> bool:
    """
    Apply learned device mappings using the door mapping service

    Args:
        df: Source dataframe
        filename: Original filename

    Returns:
        True if learned mappings were applied
    """
    svc = door_service or get_door_mapping_service()
    return svc.apply_learned_mappings(df, filename)


def save_confirmed_device_mappings(
    df: pd.DataFrame,
    filename: str,
    confirmed_mappings: Dict[str, Any],
    door_service: DoorMappingServiceProtocol | None = None,
) -> str:
    """
    Save confirmed device mappings using the door mapping service

    Args:
        df: Source dataframe
        filename: Original filename
        confirmed_mappings: User-confirmed device mappings

    Returns:
        Fingerprint ID of saved mapping
    """
    devices_list = []
    for device_id, mapping in confirmed_mappings.items():
        device_data = {"door_id": device_id}
        device_data.update(mapping)
        devices_list.append(device_data)

    svc = door_service or get_door_mapping_service()
    return svc.save_confirmed_mappings(df, filename, devices_list)


@handle_errors(service="simple_device_mapping", operation="generate_ai_device_defaults")
def generate_ai_device_defaults(
    df: pd.DataFrame,
    client_profile: str = "auto",
    door_service: DoorMappingServiceProtocol | None = None,
) -> None:
    """Generate AI-based defaults, prioritizing learned mappings"""
    learning_service = get_device_learning_service()

    if learning_service.apply_learned_mappings_to_global_store(
        df, "current_upload"
    ):
        logger.info("🎯 Applied learned mappings as defaults")
        return

    svc = door_service or get_door_mapping_service()
    result = svc.process_uploaded_data(df, client_profile)
    ai_mapping_store.clear()
    for device in result["devices"]:
        learned_mapping = learning_service.get_device_mapping_by_name(
            device["door_id"]
        )
        if learned_mapping:
            ai_mapping_store.set(device["door_id"], learned_mapping)
            logger.info(f"🎓 Used learned mapping for {device['door_id']}")
        else:
            ai_mapping_store.set(device["door_id"], device)
            logger.info(f"🤖 Generated AI mapping for {device['door_id']}")


def create_simple_device_modal_with_ai(devices: List[str]) -> dbc.Modal:
    """Create simple device mapping modal with AI learning transfer"""

    if not devices:
        devices = ["lobby_door", "office_201", "server_room", "elevator_1"]

    # Create rows for each device
    device_rows = []
    for i, device in enumerate(devices):
        ai_data = ai_mapping_store.get(device)

        default_floor = ai_data.get("floor_number")
        default_security = ai_data.get("security_level", 5)
        default_access = []
        if ai_data.get("is_entry", ai_data.get("entry")):
            default_access.append("entry")
        if ai_data.get("is_exit", ai_data.get("exit")):
            default_access.append("exit")

        default_special = []
        if ai_data.get("is_elevator", ai_data.get("elevator")):
            default_special.append("is_elevator")
        if ai_data.get("is_stairwell", ai_data.get("stairwell")):
            default_special.append("is_stairwell")
        if ai_data.get("is_fire_escape", ai_data.get("fire_escape")):
            default_special.append("is_fire_escape")
        if ai_data.get("is_restricted", ai_data.get("restricted")):
            default_special.append("is_restricted")

        col_children = [html.Strong(device)]
        if ai_data:
            col_children.append(html.Br())
            col_children.append(
                dbc.Badge("AI Suggested", color="info", className="small")
            )

        device_rows.append(
            dbc.Row(
                [
                    dbc.Col(
                        col_children,
                        width=3,  # CHANGED: from 4 to 3
                    ),
                    dbc.Col(
                        [
                            dbc.Input(
                                id={"type": "device-floor", "index": i},
                                type="number",
                                placeholder="Floor #",
                                min=0,
                                max=50,
                                value=default_floor,
                                size="sm",
                            )
                        ],
                        width=2,
                    ),
                    dbc.Col(
                        [
                            dbc.Checklist(
                                id={"type": "device-access", "index": i},
                                options=[
                                    {"label": "Entry", "value": "entry"},
                                    {"label": "Exit", "value": "exit"},
                                ],
                                value=default_access,
                                inline=True,
                            )
                        ],
                        width=2,  # CHANGED: from 3 to 2
                    ),
                    # ADD THIS COMPLETELY NEW COLUMN:
                    dbc.Col(
                        [
                            dbc.Checklist(
                                id={"type": "device-special", "index": i},
                                options=special_areas_options,
                                value=default_special,
                                inline=True,
                            )
                        ],
                        width=3,
                    ),
                    dbc.Col(
                        [
                            dbc.Input(
                                id={"type": "device-security", "index": i},
                                type="number",
                                placeholder="0-10",
                                min=0,
                                max=10,
                                value=default_security,
                                size="sm",
                            )
                        ],
                        width=2,
                    ),
                    html.Div(id={"type": "device-name", "index": i}),
                ],
                className="mb-2",
            )
        )

    device_store = html.Div(id="current-devices-list")
    suggestions_store = html.Div(id="ai-suggestions-store")
    status_div = html.Div(id="device-save-status")

    modal_children: List[Any] = [
        device_store,
        suggestions_store,
        status_div,
        dbc.Alert(
            [
                "Manually assign floor numbers and security levels to devices. ",
                (
                    html.Strong("AI suggestions have been pre-filled!")
                    if len(ai_mapping_store)
                    else "Fill in device details manually."
                ),
            ],
            color="info" if len(ai_mapping_store) else "warning",
        ),
    ]

    if len(ai_mapping_store):
        modal_children.append(
            dbc.Alert(
                [
                    html.Strong("🤖 AI Transfer: "),
                    f"Loaded {len(ai_mapping_store)} AI-learned device mappings as defaults",
                ],
                color="light",
                className="small",
            )
        )

    modal_children.extend(
        [
            dbc.Row(
                [
                    dbc.Col(
                        html.Strong("Device Name"), width=3
                    ),  # CHANGED: from 4 to 3
                    dbc.Col(html.Strong("Floor"), width=2),
                    dbc.Col(html.Strong("Access"), width=2),  # CHANGED: from 3 to 2
                    dbc.Col(html.Strong("Special Areas"), width=3),  # ADD THIS
                    dbc.Col(html.Strong("Security (0-10)"), width=2),
                ],
                className="mb-2",
            ),
            html.Hr(),
            html.Div(device_rows),
            html.Hr(),
            dbc.Alert(
                [
                    html.Strong("Security Levels: "),
                    "0-2: Public areas, 3-5: Office areas, 6-8: Restricted, 9-10: High security",
                ],
                color="light",
                className="small",
            ),
        ]
    )

    modal_body = html.Div(modal_children)

    return dbc.Modal(
        [
            dbc.ModalHeader("Device Mapping with AI Learning"),
            dbc.ModalBody(modal_body),
            dbc.ModalFooter(
                [
                    dbc.Button("Cancel", id="device-modal-cancel", color="secondary"),
                    dbc.Button("Save", id="device-modal-save", color="primary"),
                ]
            ),
        ],
        id="simple-device-modal",
        size="lg",
        is_open=False,
    )


def create_device_mapping_section(devices: List[str] | None = None) -> html.Div:
    """Return button and modal for device mapping."""

    open_button = dbc.Button(
        "Map Devices",
        id="open-device-mapping",
        color="primary",
        className="mb-3",
    )

    modal = create_simple_device_modal_with_ai(devices or [])

    return html.Div([open_button, modal])


def create_simple_device_modal(devices: List[str]) -> dbc.Modal:
    """Create simple device mapping modal"""

    if not devices:
        devices = [
            "lobby_door",
            "office_201",
            "server_room",
            "elevator_1",
        ]  # Sample devices

    # Create rows for each device
    device_rows = []
    for i, device in enumerate(devices):
        device_rows.append(
            dbc.Row(
                [
                    dbc.Col([html.Strong(device)], width=4),
                    dbc.Col(
                        [
                            dbc.Input(
                                id={"type": "device-floor", "index": i},
                                type="number",
                                placeholder="Floor #",
                                min=0,
                                max=50,
                                size="sm",
                            )
                        ],
                        width=2,
                    ),
                    dbc.Col(
                        [
                            dbc.Checklist(
                                id={"type": "device-access", "index": i},
                                options=[
                                    {"label": "Entry", "value": "entry"},
                                    {"label": "Exit", "value": "exit"},
                                ],
                                inline=True,
                            )
                        ],
                        width=3,
                    ),
                    dbc.Col(
                        [
                            dbc.Input(
                                id={"type": "device-security", "index": i},
                                type="number",
                                placeholder="0-10",
                                min=0,
                                max=10,
                                value=1,
                                size="sm",
                            )
                        ],
                        width=2,
                    ),
                    html.Div(id={"type": "device-name", "index": i}),
                ],
                className="mb-2",
            )
        )

    modal_body = html.Div(
        [
            dbc.Alert(
                "Manually assign floor numbers and security levels to devices",
                color="info",
            ),
            dbc.Row(
                [
                    dbc.Col(html.Strong("Device Name"), width=4),
                    dbc.Col(html.Strong("Floor"), width=2),
                    dbc.Col(html.Strong("Access"), width=3),
                    dbc.Col(html.Strong("Security (0-10)"), width=2),
                ],
                className="mb-2",
            ),
            html.Hr(),
            html.Div(device_rows),
            html.Hr(),
            dbc.Alert(
                [
                    html.Strong("Security Levels: "),
                    "0-2: Public areas, 3-5: Office areas, 6-8: Restricted, 9-10: High security",
                ],
                color="light",
                className="small",
            ),
        ]
    )

    return dbc.Modal(
        [
            dbc.ModalHeader("Device Mapping"),
            dbc.ModalBody(modal_body),
            dbc.ModalFooter(
                [
                    dbc.Button("Cancel", id="device-modal-cancel", color="secondary"),
                    dbc.Button("Save", id="device-modal-save", color="primary"),
                ]
            ),
        ],
        id="simple-device-modal",
        size="lg",
        is_open=False,
    )


def toggle_simple_device_modal(open_clicks, cancel_clicks, save_clicks, is_open):
    """Control the simple device modal open/close state"""
    ctx = callback_context

    if not ctx.triggered:
        return is_open

    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    logger.info(f"🎯 Modal button triggered: {button_id}")

    if button_id == "open-device-mapping" and open_clicks:
        logger.info("📂 Opening device mapping modal")
        return True
    elif button_id in ["device-modal-cancel", "device-modal-save"]:
        logger.info("🚪 Closing device mapping modal")
        return False

    return is_open


def save_user_inputs(floors, security, access, special, devices):
    """Save user inputs immediately when they change"""

    if not devices:
        return ""

    # Update global mappings with user inputs
    for i, device in enumerate(devices):
        user_floor = floors[i] if i < len(floors) and floors[i] is not None else 1
        user_security = (
            security[i] if i < len(security) and security[i] is not None else 5
        )
        user_access = access[i] if i < len(access) else []
        user_special = special[i] if i < len(special) else []

        ai_mapping_store.set(
            device,
            {
                "floor_number": user_floor,
                "security_level": user_security,
                "is_entry": "entry" in user_access,
                "is_exit": "exit" in user_access,
                "is_elevator": "is_elevator" in user_special,
                "is_stairwell": "is_stairwell" in user_special,
                "is_fire_escape": "is_fire_escape" in user_special,
                "is_restricted": "is_restricted" in user_special,
                "confidence": 1.0,
                "device_name": device,
                "ai_reasoning": "User input",
                "source": "user",
            },
        )

    return ""


def apply_ai_device_suggestions(suggestions, devices):
    """Populate UI inputs with AI-suggested values."""
    if not suggestions or not devices:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update

    floor_values = []
    access_values = []
    special_values = []
    security_values = []

    for device in devices:
        mapping = suggestions.get(device, {})

        floor_values.append(mapping.get("floor_number"))
        security_values.append(mapping.get("security_level"))

        access_list = []
        if mapping.get("is_entry", mapping.get("entry")):
            access_list.append("entry")
        if mapping.get("is_exit", mapping.get("exit")):
            access_list.append("exit")
        access_values.append(access_list)

        special_list = []
        if mapping.get("is_elevator", mapping.get("elevator")):
            special_list.append("is_elevator")
        if mapping.get("is_stairwell", mapping.get("stairwell")):
            special_list.append("is_stairwell")
        if mapping.get("is_fire_escape", mapping.get("fire_escape")):
            special_list.append("is_fire_escape")
        if mapping.get("is_restricted", mapping.get("restricted")):
            special_list.append("is_restricted")
        special_values.append(special_list)

    return floor_values, access_values, special_values, security_values


@handle_errors(service="simple_device_mapping", operation="populate_simple_device_modal")
def populate_simple_device_modal(is_open):
    """Populate modal with actual devices from uploaded data and global store."""
    if not is_open:
        return dash.no_update

    # First try to get devices from global store (preferred)
    from services.ai_mapping_store import ai_mapping_store

    store_devices = ai_mapping_store.all()

    if store_devices:
        device_list = sorted(list(store_devices.keys()))
        logger.info(
            f"📋 Found {len(device_list)} devices from global store for manual mapping"
        )
        return create_simple_device_modal_with_ai(device_list)

    # Fallback: Get devices from uploaded data
    from services.upload_data_service import get_uploaded_data

    uploaded_data = get_uploaded_data()

    if not uploaded_data:
        logger.info("📋 No uploaded data found, using sample devices")
        return create_simple_device_modal_with_ai([])

    # Extract devices from all uploaded files - check multiple column names
    all_devices = set()
    device_columns = [
        "door_id",
        "device_name",
        "DeviceName",
        "location",
        "door",
        "device",
    ]

    for filename, df in uploaded_data.items():
        for col in df.columns:
            if any(device_col.lower() in col.lower() for device_col in device_columns):
                devices = df[col].dropna().unique()
                all_devices.update(str(d) for d in devices)
                logger.info(
                    f"📋 Found {len(devices)} devices in column '{col}' from {filename}"
                )
                break  # Use first matching column

    device_list = sorted(list(all_devices))
    logger.info(f"📋 Found {len(device_list)} total devices for manual mapping")

    return create_simple_device_modal_with_ai(device_list)


def register_callbacks(
    manager: "TrulyUnifiedCallbacks",
    controller: UnifiedAnalyticsController | None = None,
) -> None:
    """Register component callbacks using the provided coordinator."""

    manager.register_callback(
        Output("simple-device-modal", "children"),
        Input("simple-device-modal", "is_open"),
        prevent_initial_call=True,
        callback_id="populate_simple_device_modal",
        component_name="simple_device_mapping",
    )(populate_simple_device_modal)

    manager.register_callback(
        Output("simple-device-modal", "is_open"),
        [
            Input("open-device-mapping", "n_clicks"),
            Input("device-modal-cancel", "n_clicks"),
            Input("device-modal-save", "n_clicks"),
        ],
        [State("simple-device-modal", "is_open")],
        prevent_initial_call=True,
        callback_id="toggle_simple_device_modal",
        component_name="simple_device_mapping",
    )(toggle_simple_device_modal)

    manager.register_callback(
        Output("device-save-status", "children"),
        [
            Input({"type": "device-floor", "index": ALL}, "value"),
            Input({"type": "device-security", "index": ALL}, "value"),
            Input({"type": "device-access", "index": ALL}, "value"),
            Input({"type": "device-special", "index": ALL}, "value"),
        ],
        [State("current-devices-list", "data")],
        prevent_initial_call=True,
        callback_id="save_user_inputs",
        component_name="simple_device_mapping",
    )(save_user_inputs)

    manager.register_callback(
        [
            Output({"type": "device-floor", "index": ALL}, "value"),
            Output({"type": "device-access", "index": ALL}, "value"),
            Output({"type": "device-special", "index": ALL}, "value"),
            Output({"type": "device-security", "index": ALL}, "value"),
        ],
        Input("ai-suggestions-store", "data"),
        [State("current-devices-list", "data")],
        prevent_initial_call=True,
        callback_id="apply_ai_device_suggestions",
        component_name="simple_device_mapping",
    )(apply_ai_device_suggestions)

    if controller is not None:
        controller.register_handler(
            "on_analysis_error",
            lambda aid, err: logger.error("Device mapping error: %s", err),
        )


__all__ = ["register_callbacks", "create_device_mapping_section"]
