"""Simple manual device mapping component"""

from dash import html, dcc
from dash._callback_context import callback_context
from core.unified_callback_coordinator import UnifiedCallbackCoordinator
from dash.dependencies import Input, Output, State, ALL
import dash_bootstrap_components as dbc
from typing import List, Dict, Any
import pandas as pd
import logging

# ADD after existing imports
from services.door_mapping_service import door_mapping_service

logger = logging.getLogger(__name__)

# Options for special device areas shared with verification component
special_areas_options = [
    {"label": "Elevator", "value": "is_elevator"},
    {"label": "Stairwell", "value": "is_stairwell"},
    {"label": "Fire Exit", "value": "is_fire_escape"},
    {"label": "Restricted", "value": "is_restricted"},
]

# Global storage for AI device mappings
_device_ai_mappings = {}


def apply_learned_device_mappings(df: pd.DataFrame, filename: str) -> bool:
    """
    Apply learned device mappings using the door mapping service

    Args:
        df: Source dataframe
        filename: Original filename

    Returns:
        True if learned mappings were applied
    """
    return door_mapping_service.apply_learned_mappings(df, filename)


def save_confirmed_device_mappings(
    df: pd.DataFrame, filename: str, confirmed_mappings: Dict[str, Any]
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

    return door_mapping_service.save_confirmed_mappings(
        df, filename, devices_list
    )


def generate_ai_device_defaults(df: pd.DataFrame, client_profile: str = "auto"):
    """Generate AI-based defaults for device mapping modal."""
    global _device_ai_mappings
    try:
        result = door_mapping_service.process_uploaded_data(df, client_profile)
        _device_ai_mappings.clear()
        for device in result["devices"]:
            _device_ai_mappings[device["door_id"]] = device
        logger.info(
            f"Generated AI defaults for {len(_device_ai_mappings)} devices"
        )
    except Exception as e:
        logger.error(f"Error generating AI device defaults: {e}")


def create_simple_device_modal_with_ai(devices: List[str]) -> dbc.Modal:
    """Create simple device mapping modal with AI learning transfer"""
    global _device_ai_mappings

    if not devices:
        devices = ["lobby_door", "office_201", "server_room", "elevator_1"]

    # Create rows for each device
    device_rows = []
    for i, device in enumerate(devices):
        ai_data = _device_ai_mappings.get(device, {})

        default_floor = ai_data.get("floor_number")
        default_security = ai_data.get("security_level", 5)
        default_access = []
        if ai_data.get("is_entry"):
            default_access.append("entry")
        if ai_data.get("is_exit"):
            default_access.append("exit")

        device_rows.append(
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Strong(device),
                            html.Br() if ai_data else None,
                            (
                                dbc.Badge(
                                    "AI Suggested", color="info", className="small"
                                )
                                if ai_data
                                else None
                            ),
                        ],
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
                                options=[
                                    {"label": "Elevator", "value": "is_elevator"},
                                    {"label": "Stairwell", "value": "is_stairwell"},
                                    {"label": "Fire Exit", "value": "is_fire_escape"},
                                ],
                                value=[],
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
                    dcc.Store(id={"type": "device-name", "index": i}, data=device),
                ],
                className="mb-2",
            )
        )

    device_store = dcc.Store(id="current-devices-list", data=devices)
    status_div = html.Div(id="device-save-status")

    modal_body = html.Div(
        [
            device_store,
            status_div,
            dbc.Alert(
                [
                    "Manually assign floor numbers and security levels to devices. ",
                    (
                        html.Strong("AI suggestions have been pre-filled!")
                        if _device_ai_mappings
                        else "Fill in device details manually."
                    ),
                ],
                color="info" if _device_ai_mappings else "warning",
            ),
            (
                dbc.Alert(
                    [
                        html.Strong(f"🤖 AI Transfer: "),
                        f"Loaded {len(_device_ai_mappings)} AI-learned device mappings as defaults",
                    ],
                    color="light",
                    className="small",
                )
                if _device_ai_mappings
                else None
            ),
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
                    dcc.Store(id={"type": "device-name", "index": i}, data=device),
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


def save_user_inputs(floors, security, access, devices):
    """Save user inputs immediately when they change"""
    global _device_ai_mappings

    if not devices:
        return ""

    # Update global mappings with user inputs
    for i, device in enumerate(devices):
        user_floor = floors[i] if i < len(floors) and floors[i] is not None else 1
        user_security = security[i] if i < len(security) and security[i] is not None else 5
        user_access = access[i] if i < len(access) else []

        _device_ai_mappings[device] = {
            "floor_number": user_floor,
            "security_level": user_security,
            "is_entry": "entry" in user_access,
            "is_exit": "exit" in user_access,
            "confidence": 1.0,
            "device_name": device,
            "ai_reasoning": "User input",
            "source": "user",
        }

    return ""


def register_callbacks(manager: UnifiedCallbackCoordinator) -> None:
    """Register component callbacks using the provided coordinator."""

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
        ],
        [State("current-devices-list", "data")],
        prevent_initial_call=True,
        callback_id="save_user_inputs",
        component_name="simple_device_mapping",
    )(save_user_inputs)


__all__ = ["register_callbacks"]
