#!/usr/bin/env python3
"""Column Header Verification Component."""

import json
import logging
import re
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Protocol

import dash
import dash_bootstrap_components as dbc
import pandas as pd
from dash import ALL, MATCH, Input, Output, State, dcc, html

from components.plugin_adapter import ComponentPluginAdapter
from services.data_enhancer import (
    get_ai_column_suggestions as simple_column_suggestions,
)

try:
    from analytics.controllers import UnifiedAnalyticsController
except ImportError:  # pragma: no cover - optional dependency
    UnifiedAnalyticsController = None

if TYPE_CHECKING:  # pragma: no cover - for type hints only
    from core.truly_unified_callbacks import TrulyUnifiedCallbacks


class ColumnVerifierProtocol(Protocol):
    """Protocol for column verification helpers."""

    def create_column_verification_modal(self, file_info: Dict[str, Any]) -> Any: ...

    def register_callbacks(
        self,
        manager: "TrulyUnifiedCallbacks",
        controller: Optional[UnifiedAnalyticsController] = None,
    ) -> None: ...


logger = logging.getLogger(__name__)
adapter = ComponentPluginAdapter()

# Standard field options for dropdown
STANDARD_FIELD_OPTIONS = [
    {"label": "Person/User ID", "value": "person_id"},
    {"label": "Door/Location ID", "value": "door_id"},
    {"label": "Timestamp", "value": "timestamp"},
    {"label": "Access Result", "value": "access_result"},
    {"label": "Token/Badge ID", "value": "token_id"},
    {"label": "Badge Status", "value": "badge_status"},
    {"label": "Device Status", "value": "device_status"},
    {"label": "Event Type", "value": "event_type"},
    {"label": "Building/Floor", "value": "building_id"},
    {"label": "Entry/Exit Type", "value": "entry_type"},
    {"label": "Duration", "value": "duration"},
    {"label": "Ignore Column", "value": "ignore"},
    {"label": "Other/Custom", "value": "other"},
]


def create_column_verification_modal(file_info: Dict[str, Any]) -> dbc.Modal:
    """Complete modal with data preview and AI mapping table"""
    filename = file_info.get("filename", "Unknown File")
    columns = file_info.get("columns", [])
    ai_suggestions = file_info.get("ai_suggestions", {})

    if not columns:
        return html.Div(id="empty-column-modal")

    # Create column mapping table with AI suggestions
    table_rows = []
    for i, column in enumerate(columns):
        ai_suggestion = ai_suggestions.get(column, {})
        suggested_field = ai_suggestion.get("field", "")
        confidence = ai_suggestion.get("confidence", 0.0)
        default_value = suggested_field if suggested_field else None

        # Color coding for confidence
        confidence_class = (
            "text-danger"
            if confidence < 0.5
            else "text-success" if confidence > 0.7 else "text-warning"
        )
        dropdown_style = {"border": "2px solid red"} if confidence < 0.5 else {}

        table_rows.append(
            html.Tr(
                [
                    html.Td(
                        [
                            html.Strong(column),
                            html.Br(),
                            html.Small(
                                f"AI Confidence: {confidence:.0%}",
                                className=confidence_class,
                            ),
                        ]
                    ),
                    html.Td(
                        [
                            dcc.Dropdown(
                                id={"type": "column-mapping", "index": i},
                                options=STANDARD_FIELD_OPTIONS,
                                placeholder=f"Map {column} to...",
                                value=default_value,
                                style=dropdown_style,
                            )
                        ]
                    ),
                ]
            )
        )

    modal_body = html.Div(
        [
            html.H5(f"Column Mapping: {filename}"),
            html.P(f"Found {len(columns)} columns"),
            html.H6("AI Column Mapping:", className="mb-2"),
            dbc.Table(
                [
                    html.Thead(
                        [
                            html.Tr(
                                [
                                    html.Th("Column Name & AI Confidence"),
                                    html.Th("Map to Standard Field"),
                                ]
                            )
                        ]
                    ),
                    html.Tbody(table_rows),
                ],
                striped=True,
                hover=True,
                responsive=True,
                className="mb-3",
            ),
        ]
    )

    return dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle(f"AI Column Mapping - {filename}")),
            dbc.ModalBody(modal_body),
            dbc.ModalFooter(
                [
                    dbc.Button(
                        "Cancel",
                        id="column-verify-cancel",
                        color="secondary",
                        className="me-2",
                    ),
                    dbc.Button("Confirm", id="column-verify-confirm", color="success"),
                ]
            ),
        ],
        id="column-verification-modal",
        size="xl",
        is_open=False,
    )


def create_verification_interface(
    columns: List[str], sample_data: Dict, ai_suggestions: Dict
) -> html.Div:
    """Simple column verification - CSV headers in dropdowns"""

    if not columns:
        return dbc.Alert("No columns found in uploaded file", color="warning")

    # Create simple mapping rows
    mapping_rows = []

    for i, column in enumerate(columns):
        # Get AI suggestion
        ai_suggestion = ai_suggestions.get(column, {})
        suggested_field = ai_suggestion.get("field", "")
        confidence = ai_suggestion.get("confidence", 0.0)

        # Simple row for each standard field
        mapping_rows.append(
            dbc.Row(
                [
                    # Standard field name
                    dbc.Col(
                        [dbc.Label(f"Map '{column}' to:", className="fw-bold")], width=4
                    ),
                    # Dropdown with CSV column headers
                    dbc.Col(
                        [
                            dcc.Dropdown(
                                id={"type": "column-mapping", "index": i},
                                options=STANDARD_FIELD_OPTIONS,
                                value=suggested_field if confidence > 0.5 else None,
                                placeholder=f"Map '{column}' to standard field",
                                className="mb-2",
                            )
                        ],
                        width=6,
                    ),
                    # Confidence
                    dbc.Col(
                        [
                            dbc.Badge(
                                f"{confidence:.0%}",
                                color=(
                                    "success"
                                    if confidence > 0.7
                                    else "warning" if confidence > 0.4 else "secondary"
                                ),
                            )
                        ],
                        width=2,
                    ),
                ],
                className="mb-3",
            )
        )

    return html.Div(
        [
            dbc.Alert(
                f"Found {len(columns)} columns: {', '.join(columns)}",
                color="info",
                className="mb-4",
            ),
            html.H5("Map your CSV columns:", className="mb-3"),
            html.Div(mapping_rows),
        ]
    )


def create_column_mapping_card(
    column_index: int,
    column_name: str,
    sample_values: List,
    ai_suggestion: str,
    confidence_badge: html.Span,
) -> dbc.Card:
    """Create individual column mapping card"""
    suggested_option = next(
        (opt for opt in STANDARD_FIELD_OPTIONS if opt["value"] == ai_suggestion), None
    )
    default_value = ai_suggestion if suggested_option else "other"
    return dbc.Card(
        [
            dbc.CardHeader(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.H6(
                                        [
                                            html.Code(
                                                column_name,
                                                className="bg-light px-2 py-1 rounded",
                                            )
                                        ],
                                        className="mb-0",
                                    )
                                ],
                                width=8,
                            ),
                            dbc.Col([confidence_badge], width=4, className="text-end"),
                        ]
                    )
                ]
            ),
            dbc.CardBody(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Label(
                                        "Map to Standard Field:", className="fw-bold"
                                    ),
                                    dcc.Dropdown(
                                        id={
                                            "type": "column-mapping",
                                            "index": column_index,
                                        },
                                        options=STANDARD_FIELD_OPTIONS,
                                        value=default_value,
                                        clearable=False,
                                        className="mb-3",
                                    ),
                                    html.Div(
                                        [
                                            dbc.Label("Custom Field Name:"),
                                            dbc.Input(
                                                id={
                                                    "type": "custom-field",
                                                    "index": column_index,
                                                },
                                                placeholder=(
                                                    "Enter custom field name..."
                                                ),
                                                style={"display": "none"},
                                            ),
                                        ],
                                        id={
                                            "type": "custom-field-container",
                                            "index": column_index,
                                        },
                                    ),
                                ],
                                width=6,
                            ),
                            dbc.Col(
                                [
                                    dbc.Label("Sample Values:", className="fw-bold"),
                                    html.Div(
                                        [
                                            dbc.Badge(
                                                (
                                                    str(value)[:50] + "..."
                                                    if len(str(value)) > 50
                                                    else str(value)
                                                ),
                                                color="light",
                                                text_color="dark",
                                                className="me-1 mb-1",
                                            )
                                            for value in sample_values[:5]
                                        ]
                                        if sample_values
                                        else [
                                            html.Small(
                                                "No sample data available",
                                                className="text-muted",
                                            )
                                        ]
                                    ),
                                ],
                                width=6,
                            ),
                        ]
                    )
                ]
            ),
        ],
        className="mb-3",
    )


def create_confidence_badge(confidence: float) -> html.Span:
    """Create confidence badge based on AI confidence score"""
    if confidence >= 0.8:
        return dbc.Badge(
            f"High {confidence:.0%}", color="success", className="confidence-badge"
        )
    elif confidence >= 0.5:
        return dbc.Badge(
            f"Medium {confidence:.0%}", color="warning", className="confidence-badge"
        )
    elif confidence > 0:
        return dbc.Badge(
            f"Low {confidence:.0%}", color="danger", className="confidence-badge"
        )
    else:
        return dbc.Badge(
            "No AI Suggestion", color="secondary", className="confidence-badge"
        )


def get_ai_column_suggestions(
    df: pd.DataFrame, filename: str
) -> Dict[str, Dict[str, Any]]:
    """Return AI column mapping suggestions using the plugin adapter."""
    logger.info(f"🤖 Analyzing columns for {filename}:")
    logger.info(f"   Columns found: {list(df.columns)}")
    try:
        return adapter.get_ai_column_suggestions(df, filename)
    except Exception as e:  # pragma: no cover - defensive
        logger.error(f"Error getting AI suggestions for {filename}: {e}")
        return _analyze_file_specific_columns(df, filename)


def _analyze_file_specific_columns(
    df: pd.DataFrame, filename: str
) -> Dict[str, Dict[str, Any]]:
    """
    Analyze THIS specific file's columns and data to suggest mappings
    This is where the AI learns patterns from actual data
    """
    suggestions = {}

    logger.info(f"📊 Analyzing file-specific patterns in {filename}:")

    for column in df.columns:
        column_lower = column.lower().strip()
        sample_values = df[column].dropna().head(10).astype(str).tolist()

        logger.info(f"   🔍 Analyzing '{column}':")
        logger.info(f"      Sample values: {sample_values[:3]}")

        suggestion = {"field": "", "confidence": 0.0}

        # Analyze column name patterns
        name_confidence = _analyze_column_name(column_lower)
        if name_confidence["field"]:
            suggestion = name_confidence
            logger.info(
                "      📝 Name pattern: %s (%.0f%%)",
                suggestion["field"],
                suggestion["confidence"] * 100,
            )

        # Analyze sample data patterns
        data_confidence = _analyze_sample_data(sample_values, column)
        if data_confidence["confidence"] > suggestion["confidence"]:
            suggestion = data_confidence
            logger.info(
                "      📈 Data pattern: %s (%.0f%%)",
                suggestion["field"],
                suggestion["confidence"] * 100,
            )

        # Store the best suggestion
        suggestions[column] = suggestion

    return suggestions


def _analyze_column_name(column_name: str) -> Dict[str, Any]:
    """Analyze column name for mapping hints"""

    # Exact matches (high confidence)
    exact_matches = {
        "timestamp": ["timestamp", "time", "datetime", "date_time", "event_time"],
        "person_id": ["person_id", "user_id", "person id", "user id"],
        "door_id": ["door_id", "door id", "device name", "location"],
        "access_result": ["access_result", "result", "access result", "status"],
        "token_id": ["token_id", "token id", "badge_id", "card_id"],
    }

    for field, patterns in exact_matches.items():
        if column_name in patterns:
            return {"field": field, "confidence": 0.95}

    # Partial matches (medium confidence)
    partial_matches = {
        "person_id": ["person", "user", "employee", "name", "who"],
        "door_id": ["door", "location", "device", "room", "gate", "where"],
        "timestamp": ["time", "date", "when", "stamp"],
        "access_result": ["result", "status", "outcome", "access", "granted", "denied"],
        "token_id": ["token", "badge", "card", "id"],
    }

    for field, keywords in partial_matches.items():
        if any(keyword in column_name for keyword in keywords):
            return {"field": field, "confidence": 0.7}

    return {"field": "", "confidence": 0.0}


def _analyze_sample_data(sample_values: List[str], column_name: str) -> Dict[str, Any]:
    """Analyze sample data to infer column type"""

    if not sample_values:
        return {"field": "", "confidence": 0.0}

    # Check for timestamp patterns
    timestamp_patterns = [
        r"\d{4}-\d{2}-\d{2}",  # 2023-03-22
        r"\d{2}/\d{2}/\d{4}",  # 03/22/2023
        r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}",  # 2023-03-22 01:14:16
    ]

    for value in sample_values[:5]:
        for pattern in timestamp_patterns:
            if re.search(pattern, str(value)):
                return {"field": "timestamp", "confidence": 0.9}

    # Check for access result patterns
    access_results = [
        "granted",
        "denied",
        "access granted",
        "access denied",
        "success",
        "fail",
    ]
    for value in sample_values:
        if any(result in str(value).lower() for result in access_results):
            return {"field": "access_result", "confidence": 0.85}

    # Check for ID patterns (letters + numbers)
    id_pattern = r"^[A-Z]\d+$|^[A-Z]+\d+$"
    id_matches = sum(1 for value in sample_values if re.match(id_pattern, str(value)))
    if id_matches >= len(sample_values) * 0.8:  # 80% match
        if "person" in column_name.lower() or "user" in column_name.lower():
            return {"field": "person_id", "confidence": 0.8}
        elif "token" in column_name.lower() or "badge" in column_name.lower():
            return {"field": "token_id", "confidence": 0.8}

    # Check for door/device patterns
    door_keywords = ["door", "gate", "entrance", "exit", "room", "floor"]
    for value in sample_values:
        if any(keyword in str(value).lower() for keyword in door_keywords):
            return {"field": "door_id", "confidence": 0.75}

    return {"field": "", "confidence": 0.0}


def _get_fallback_suggestions(columns: List[str]) -> Dict[str, Dict[str, Any]]:
    """Fallback column suggestions using simple heuristics"""
    return simple_column_suggestions(columns)


def save_verified_mappings(
    filename: str, column_mappings: Dict[str, str], metadata: Dict[str, Any]
) -> bool:
    """
    Save verified column mappings for AI training - FILE-SPECIFIC LEARNING

    Args:
        filename: Name of the uploaded file
        column_mappings: Dict of column_name -> standard_field
        metadata: Additional metadata (data_source_type, quality, etc.)

    Returns:
        Success status
    """
    try:
        # Enhanced training data with file-specific information
        training_data = {
            "filename": filename,
            "file_type": filename.split(".")[-1].lower(),
            "timestamp": datetime.now().isoformat(),
            "mappings": column_mappings,
            "metadata": metadata,
            "verified_by_user": True,
            "learning_context": {
                "columns_in_file": list(column_mappings.keys()),
                "mapped_fields": list(column_mappings.values()),
                "num_columns": len(column_mappings),
                "file_size_category": metadata.get("file_size_category", "unknown"),
            },
        }

        logger.info(f"💾 Saving training data for {filename}:")
        logger.info(f"   Mappings: {column_mappings}")
        logger.info(f"   Context: {training_data['learning_context']}")

        # Try to save using the plugin adapter
        if not adapter.save_verified_mappings(filename, column_mappings, metadata):
            logger.info("AI system save failed or unavailable")

        # Save to file-specific training data
        try:
            import os

            os.makedirs("data/training", exist_ok=True)

            # Create file-specific training log
            today = datetime.now().strftime("%Y%m%d")
            training_file = f"data/training/column_mappings_{today}.jsonl"

            with open(training_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(training_data) + "\n")

            logger.info(f"Training data appended to {training_file}")
            logger.info(f"✅ File-specific training data saved to {training_file}")

        except Exception as file_e:
            logger.warning(f"Failed to save training file: {file_e}")
            logger.info(f"⚠️ Training file save failed: {file_e}")

        return True

    except Exception as e:
        logger.error(f"Error saving verified mappings: {e}")
        logger.info(f"❌ Error saving mappings: {e}")
        return False


def toggle_custom_field(selected_value):
    """Show custom field input when 'other' is selected"""
    if selected_value == "other":
        return {"display": "block"}
    else:
        return {"display": "none"}


def save_column_mappings_callback(
    n_clicks: int | None,
    column_values: List[str | None],
    ids: List[Dict[str, Any]],
    custom_values: List[str | None],
    uploaded_files_data: Dict[str, Any] | None,
) -> tuple[str, str]:
    """Persist verified column mappings when the save button is clicked."""

    if not n_clicks:
        return dash.no_update, dash.no_update

    if not uploaded_files_data:
        logger.warning("No uploaded file data found for saving mappings")
        return "❌ Error", "danger"

    # Determine file info from store
    file_info = {}
    filename = "unknown.csv"
    if "current_file_info" in uploaded_files_data:
        file_info = uploaded_files_data.get("current_file_info", {})
        filename = file_info.get("filename", filename)
    elif uploaded_files_data:
        first_key = next(iter(uploaded_files_data.keys()))
        file_info = uploaded_files_data.get(first_key, {})
        filename = file_info.get("filename", first_key)

    columns = file_info.get("column_names", file_info.get("columns", []))
    metadata = file_info.get("metadata", {})

    mappings: Dict[str, str] = {}
    for i, value in enumerate(column_values or []):
        if not value or i >= len(columns):
            continue

        mapped_field = value
        if value == "other":
            custom = custom_values[i] if i < len(custom_values) else None
            if not custom:
                continue
            mapped_field = custom

        mappings[columns[i]] = mapped_field

    success = save_verified_mappings(filename, mappings, metadata)

    if success:
        return "✅ Confirmed", "success"

    return "❌ Error", "danger"


def register_callbacks(
    manager: "TrulyUnifiedCallbacks",
    controller: Optional[UnifiedAnalyticsController] = None,
) -> None:
    """Register component callbacks using the coordinator."""

    manager.register_callback(
        Output({"type": "custom-field", "index": MATCH}, "style"),
        Input({"type": "column-mapping", "index": MATCH}, "value"),
        prevent_initial_call=True,
        callback_id="toggle_custom_field",
        component_name="column_verification",
    )(toggle_custom_field)

    manager.register_callback(
        [
            Output("save-column-mappings", "children"),
            Output("save-column-mappings", "color"),
        ],
        Input("save-column-mappings", "n_clicks"),
        [
            State({"type": "column-mapping", "index": ALL}, "value"),
            State({"type": "column-mapping", "index": ALL}, "id"),
            State({"type": "custom-field", "index": ALL}, "value"),
            State("uploaded-files-store", "data"),
        ],
        prevent_initial_call=True,
        callback_id="save_column_mappings",
        component_name="column_verification",
    )(save_column_mappings_callback)
    if controller is not None:
        controller.register_handler(
            "on_analysis_error",
            lambda aid, err: logger.error("Column verification error: %s", err),
        )


# ---------------------------------------------------------------------------
# Reversed Mapping Callbacks
# ---------------------------------------------------------------------------


__all__ = [
    "create_complete_column_section",
    "create_column_display_section",
    "create_column_verification_modal",
    "get_ai_column_suggestions",
    "save_verified_mappings",
    "register_callbacks",
]


def create_column_display_section(file_info: Dict[str, Any]) -> html.Div:
    """Create main column display with preview and AI mapping."""
    columns = file_info.get("columns", [])
    column_names = file_info.get("column_names", columns)
    ai_suggestions = file_info.get("ai_suggestions", {})

    if not column_names:
        return dbc.Alert("No columns found", color="warning")

    # Column listing
    column_list = html.Div(
        [html.H5("Column Names:"), html.Ul([html.Li(col) for col in column_names])]
    )

    # AI mapping display table
    ai_mapping_section = html.Div()
    if ai_suggestions:
        mapping_rows = []
        for column, suggestion in ai_suggestions.items():
            confidence = suggestion.get("confidence", 0.0)
            field = suggestion.get("field", "No suggestion")

            # Color code confidence
            if confidence < 0.5:
                confidence_class = "text-danger"
                confidence_text = f"{confidence:.0%} (Low)"
            elif confidence > 0.7:
                confidence_class = "text-success"
                confidence_text = f"{confidence:.0%} (High)"
            else:
                confidence_class = "text-warning"
                confidence_text = f"{confidence:.0%} (Medium)"

            mapping_rows.append(
                html.Tr(
                    [
                        html.Td(html.Strong(column)),
                        html.Td(field if field else "No suggestion"),
                        html.Td(html.Span(confidence_text, className=confidence_class)),
                    ]
                )
            )

        ai_mapping_section = html.Div(
            [
                html.H5("AI Column Mapping:"),
                html.P(f"Found {len(ai_suggestions)} AI suggestions"),
                dbc.Table(
                    [
                        html.Thead(
                            [
                                html.Tr(
                                    [
                                        html.Th("Column Name"),
                                        html.Th("AI Suggested Mapping"),
                                        html.Th("Confidence Level"),
                                    ]
                                )
                            ]
                        ),
                        html.Tbody(mapping_rows),
                    ],
                    striped=True,
                    hover=True,
                    responsive=True,
                ),
            ]
        )
    else:
        ai_mapping_section = dbc.Alert("No AI suggestions available", color="info")

    return html.Div([column_list, html.Hr(), ai_mapping_section])


def create_complete_column_section(
    file_info: Dict[str, Any], df: pd.DataFrame = None
) -> html.Div:
    """Create complete column section with preview and mapping interface."""
    columns = file_info.get("column_names", file_info.get("columns", []))
    ai_suggestions = file_info.get("ai_suggestions", {})

    if not columns:
        return dbc.Alert("No columns found", color="warning")

    sections = []

    # Column listing
    sections.append(
        html.Div(
            [
                html.H5("Column Names:"),
                html.Ul([html.Li(html.Strong(col)) for col in columns]),
            ]
        )
    )

    # Data preview if DataFrame provided
    if df is not None and not df.empty:
        preview_data = df.head(5)
        preview_rows = []
        for _, row in preview_data.iterrows():
            preview_rows.append(html.Tr([html.Td(str(val)) for val in row]))

        sections.append(
            html.Div(
                [
                    html.H5("Data Preview (first 5 rows):"),
                    dbc.Table(
                        [
                            html.Thead([html.Tr([html.Th(col) for col in columns])]),
                            html.Tbody(preview_rows),
                        ],
                        striped=True,
                        bordered=True,
                        size="sm",
                        className="mb-4",
                    ),
                ]
            )
        )

    # AI Column Mapping Interface - Two Column Table
    if ai_suggestions:
        table_rows = []
        for i, column in enumerate(columns):
            ai_suggestion = ai_suggestions.get(column, {})
            suggested_field = ai_suggestion.get("field", "")
            confidence = ai_suggestion.get("confidence", 0.0)
            default_value = suggested_field if suggested_field else None

            # Color coding for confidence
            confidence_class = (
                "text-danger"
                if confidence < 0.5
                else "text-success" if confidence > 0.7 else "text-warning"
            )
            dropdown_style = {"border": "2px solid red"} if confidence < 0.5 else {}

            table_rows.append(
                html.Tr(
                    [
                        html.Td(
                            [
                                html.Strong(column),
                                html.Br(),
                                html.Small(
                                    f"AI: {suggested_field} ({confidence:.0%})",
                                    className=confidence_class,
                                ),
                            ]
                        ),
                        html.Td(
                            [
                                dcc.Dropdown(
                                    id={"type": "column-mapping", "index": i},
                                    options=STANDARD_FIELD_OPTIONS,
                                    placeholder=f"Map {column} to...",
                                    value=default_value,
                                    style=dropdown_style,
                                )
                            ]
                        ),
                    ]
                )
            )

        sections.append(
            html.Div(
                [
                    html.H5("AI Column Mapping:"),
                    html.P("Review AI suggestions and adjust mappings as needed:"),
                    dbc.Table(
                        [
                            html.Thead(
                                [
                                    html.Tr(
                                        [
                                            html.Th("Column Name & AI Suggestion"),
                                            html.Th("Manual Mapping Override"),
                                        ]
                                    )
                                ]
                            ),
                            html.Tbody(table_rows),
                        ],
                        striped=True,
                        hover=True,
                        responsive=True,
                        className="mb-3",
                    ),
                    dbc.Button(
                        "Save Column Mappings",
                        id="save-column-mappings",
                        color="primary",
                        size="lg",
                    ),
                ]
            )
        )
    else:
        sections.append(
            html.Div(
                [
                    html.H5("AI Column Mapping:"),
                    dbc.Alert("No AI suggestions available", color="info"),
                ]
            )
        )

    return html.Div(sections)
