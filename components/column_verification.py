#!/usr/bin/env python3
"""
Column Header Verification Component
Allows manual verification of AI-suggested column mappings
Feeds back to AI training data
"""

import pandas as pd
from dash import html, dcc, callback, Input, Output, State, ALL, MATCH
from core.unified_callback_coordinator import UnifiedCallbackCoordinator
import dash
import dash_bootstrap_components as dbc
from typing import Dict, List, Any
import logging
from datetime import datetime
import json
import re

logger = logging.getLogger(__name__)

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
    {"label": "Other/Custom", "value": "other"}
]

def create_column_verification_modal(file_info: Dict[str, Any]) -> dbc.Modal:
    """Simple modal WITH AI training components"""
    filename = file_info.get('filename', 'Unknown File')
    columns = file_info.get('columns', [])
    ai_suggestions = file_info.get('ai_suggestions', {})

    if not columns:
        return html.Div()

    # Create simple table with AI suggestions
    table_rows = []
    for i, column in enumerate(columns):
        ai_suggestion = ai_suggestions.get(column, {})
        suggested_field = ai_suggestion.get('field', '')
        confidence = ai_suggestion.get('confidence', 0.0)
        default_value = suggested_field if suggested_field else None

        table_rows.append(
            html.Tr([
                html.Td([
                    html.Strong(column),
                    html.Br(),
                    html.Small(
                        f"AI Confidence: {confidence:.0%}",
                        className="text-muted" if confidence < 0.5 else "text-success"
                    )
                ]),
                html.Td(
                    dcc.Dropdown(
                        id={"type": "column-mapping", "index": i},
                        options=STANDARD_FIELD_OPTIONS,
                        placeholder=f"Map {column} to...",
                        value=default_value
                    )
                )
            ])
        )

    modal_body = html.Div([
        html.H5(f"Map columns from {filename}"),
        dbc.Alert([
            "AI has analyzed your columns and made suggestions. ",
            dbc.Button(
                "Use All AI Suggestions",
                id="column-verify-ai-auto",
                color="info",
                size="sm",
                className="ms-2",
            ),
        ], color="info", className="mb-3"),

        dbc.Table([
            html.Thead([
                html.Tr([html.Th("CSV Column"), html.Th("Maps To")])
            ]),
            html.Tbody(table_rows)
        ], striped=True),

        dbc.Card([
            dbc.CardHeader(html.H6("Help AI Learn", className="mb-0")),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Data Source Type:"),
                        dcc.Dropdown(
                            id="training-data-source-type",
                            options=[
                                {"label": "Corporate Access Control", "value": "corporate"},
                                {"label": "Educational Institution", "value": "education"},
                                {"label": "Healthcare Facility", "value": "healthcare"},
                                {"label": "Manufacturing/Industrial", "value": "manufacturing"},
                                {"label": "Retail/Commercial", "value": "retail"},
                                {"label": "Government/Public", "value": "government"},
                                {"label": "Other", "value": "other"},
                            ],
                            value="corporate",
                        ),
                    ], width=6),
                    dbc.Col([
                        dbc.Label("Data Quality:"),
                        dcc.Dropdown(
                            id="training-data-quality",
                            options=[
                                {"label": "Excellent - Clean, consistent data", "value": "excellent"},
                                {"label": "Good - Minor inconsistencies", "value": "good"},
                                {"label": "Average - Some data issues", "value": "average"},
                                {"label": "Poor - Many inconsistencies", "value": "poor"},
                            ],
                            value="good",
                        ),
                    ], width=6),
                ])
            ])
        ], className="mt-3"),
    ])

    return dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle(f"AI Column Mapping - {filename}")),
        dbc.ModalBody(modal_body, id="modal-body"),
        dbc.ModalFooter([
            dbc.Button("Cancel", id="column-verify-cancel", color="secondary", className="me-2"),
            dbc.Button("Confirm & Train AI", id="column-verify-confirm", color="success"),
        ])
    ],
    id="column-verification-modal",
    size="xl",
    is_open=False,
    )

def create_verification_interface(columns: List[str], sample_data: Dict, ai_suggestions: Dict) -> html.Div:
    """Simple column verification - CSV headers in dropdowns"""

    if not columns:
        return dbc.Alert("No columns found in uploaded file", color="warning")

    # Create simple mapping rows
    mapping_rows = []

    for i, column in enumerate(columns):
        # Get AI suggestion
        ai_suggestion = ai_suggestions.get(column, {})
        suggested_field = ai_suggestion.get('field', '')
        confidence = ai_suggestion.get('confidence', 0.0)

        # Simple row for each standard field
        mapping_rows.append(
            dbc.Row([
                # Standard field name
                dbc.Col([
                    dbc.Label(f"Map '{column}' to:", className="fw-bold")
                ], width=4),

                # Dropdown with CSV column headers
                dbc.Col([
                    dcc.Dropdown(
                        id={"type": "column-mapping", "index": i},
                        options=[{"label": col, "value": col} for col in columns] +
                               [{"label": "Skip this column", "value": "ignore"}],
                        value=column if confidence > 0.5 else None,
                        placeholder=f"Select column for {column}",
                        className="mb-2"
                    )
                ], width=6),

                # Confidence
                dbc.Col([
                    dbc.Badge(f"{confidence:.0%}",
                             color="success" if confidence > 0.7 else "warning" if confidence > 0.4 else "secondary")
                ], width=2)

            ], className="mb-3")
        )

    return html.Div([
        dbc.Alert(f"Found {len(columns)} columns: {', '.join(columns)}", color="info", className="mb-4"),
        html.H5("Map your CSV columns:", className="mb-3"),
        html.Div(mapping_rows)
    ])

def create_column_mapping_card(column_index: int, column_name: str, sample_values: List, ai_suggestion: str, confidence_badge: html.Span) -> dbc.Card:
    """Create individual column mapping card"""
    suggested_option = next((opt for opt in STANDARD_FIELD_OPTIONS if opt["value"] == ai_suggestion), None)
    default_value = ai_suggestion if suggested_option else "other"
    return dbc.Card([
        dbc.CardHeader([
            dbc.Row([
                dbc.Col([
                    html.H6([
                        html.Code(column_name, className="bg-light px-2 py-1 rounded")
                    ], className="mb-0")
                ], width=8),
                dbc.Col([
                    confidence_badge
                ], width=4, className="text-end")
            ])
        ]),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dbc.Label("Map to Standard Field:", className="fw-bold"),
                    dcc.Dropdown(
                        id={"type": "column-mapping", "index": column_index},
                        options=STANDARD_FIELD_OPTIONS,
                        value=default_value,
                        clearable=False,
                        className="mb-3"
                    ),
                    html.Div([
                        dbc.Label("Custom Field Name:"),
                        dbc.Input(
                            id={"type": "custom-field", "index": column_index},
                            placeholder="Enter custom field name...",
                            style={"display": "none"}
                        )
                    ], id={"type": "custom-field-container", "index": column_index})
                ], width=6),
                dbc.Col([
                    dbc.Label("Sample Values:", className="fw-bold"),
                    html.Div([
                        dbc.Badge(
                            str(value)[:50] + "..." if len(str(value)) > 50 else str(value),
                            color="light",
                            text_color="dark",
                            className="me-1 mb-1"
                        ) for value in sample_values[:5]
                    ] if sample_values else [
                        html.Small("No sample data available", className="text-muted")
                    ])
                ], width=6)
            ])
        ])
    ], className="mb-3")

def create_confidence_badge(confidence: float) -> html.Span:
    """Create confidence badge based on AI confidence score"""
    if confidence >= 0.8:
        return dbc.Badge(f"High {confidence:.0%}", color="success", className="confidence-badge")
    elif confidence >= 0.5:
        return dbc.Badge(f"Medium {confidence:.0%}", color="warning", className="confidence-badge")
    elif confidence > 0:
        return dbc.Badge(f"Low {confidence:.0%}", color="danger", className="confidence-badge")
    else:
        return dbc.Badge("No AI Suggestion", color="secondary", className="confidence-badge")

def get_ai_column_suggestions(df: pd.DataFrame, filename: str) -> Dict[str, Dict[str, Any]]:
    """
    Get AI suggestions for column mappings based on THIS specific CSV file
    Integrates with existing AI classification plugin
    """
    suggestions = {}

    logger.info(f"🤖 Analyzing columns for {filename}:")
    logger.info(f"   Columns found: {list(df.columns)}")

    try:
        # Try to use the existing AI classification plugin
        from plugins.ai_classification.plugin import AIClassificationPlugin
        from plugins.ai_classification.config import get_ai_config

        ai_plugin = AIClassificationPlugin(get_ai_config())
        if ai_plugin.start():
            headers = df.columns.tolist()
            session_id = f"file_{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            logger.info(f"   🧠 Getting AI suggestions for: {headers}")

            # Get AI mapping suggestions for THIS specific file
            ai_result = ai_plugin.map_columns(headers, session_id)

            if ai_result.get('success'):
                suggested_mapping = ai_result.get('suggested_mapping', {})
                confidence_scores = ai_result.get('confidence_scores', {})

                for header in headers:
                    if header in suggested_mapping:
                        suggestions[header] = {
                            'field': suggested_mapping[header],
                            'confidence': confidence_scores.get(header, 0.0)
                        }
                        logger.info(f"      ✅ {header} -> {suggested_mapping[header]} ({confidence_scores.get(header, 0):.0%})")
                    else:
                        suggestions[header] = {'field': '', 'confidence': 0.0}
                        logger.info(f"      ❓ {header} -> No AI suggestion")

                logger.info(f"AI suggestions generated for {len(suggestions)} columns in {filename}")
            else:
                logger.warning(f"AI mapping failed for {filename}, using file-specific analysis")
                suggestions = _analyze_file_specific_columns(df, filename)
        else:
            logger.warning(f"AI plugin failed to start for {filename}, using file-specific analysis")
            suggestions = _analyze_file_specific_columns(df, filename)

    except Exception as e:
        logger.error(f"Error getting AI suggestions for {filename}: {e}")
        suggestions = _analyze_file_specific_columns(df, filename)

    return suggestions


def _analyze_file_specific_columns(df: pd.DataFrame, filename: str) -> Dict[str, Dict[str, Any]]:
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

        suggestion = {'field': '', 'confidence': 0.0}

        # Analyze column name patterns
        name_confidence = _analyze_column_name(column_lower)
        if name_confidence['field']:
            suggestion = name_confidence
            logger.info(f"      📝 Name pattern: {suggestion['field']} ({suggestion['confidence']:.0%})")

        # Analyze sample data patterns  
        data_confidence = _analyze_sample_data(sample_values, column)
        if data_confidence['confidence'] > suggestion['confidence']:
            suggestion = data_confidence
            logger.info(f"      📈 Data pattern: {suggestion['field']} ({suggestion['confidence']:.0%})")

        # Store the best suggestion
        suggestions[column] = suggestion

    return suggestions


def _analyze_column_name(column_name: str) -> Dict[str, Any]:
    """Analyze column name for mapping hints"""

    # Exact matches (high confidence)
    exact_matches = {
        'timestamp': ['timestamp', 'time', 'datetime', 'date_time', 'event_time'],
        'person_id': ['person_id', 'user_id', 'person id', 'user id'],
        'door_id': ['door_id', 'door id', 'device name', 'location'],
        'access_result': ['access_result', 'result', 'access result', 'status'],
        'token_id': ['token_id', 'token id', 'badge_id', 'card_id']
    }

    for field, patterns in exact_matches.items():
        if column_name in patterns:
            return {'field': field, 'confidence': 0.95}

    # Partial matches (medium confidence)
    partial_matches = {
        'person_id': ['person', 'user', 'employee', 'name', 'who'],
        'door_id': ['door', 'location', 'device', 'room', 'gate', 'where'],
        'timestamp': ['time', 'date', 'when', 'stamp'],
        'access_result': ['result', 'status', 'outcome', 'access', 'granted', 'denied'],
        'token_id': ['token', 'badge', 'card', 'id']
    }

    for field, keywords in partial_matches.items():
        if any(keyword in column_name for keyword in keywords):
            return {'field': field, 'confidence': 0.7}

    return {'field': '', 'confidence': 0.0}


def _analyze_sample_data(sample_values: List[str], column_name: str) -> Dict[str, Any]:
    """Analyze sample data to infer column type"""

    if not sample_values:
        return {'field': '', 'confidence': 0.0}

    # Check for timestamp patterns
    timestamp_patterns = [
        r'\d{4}-\d{2}-\d{2}',  # 2023-03-22
        r'\d{2}/\d{2}/\d{4}',  # 03/22/2023
        r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}',  # 2023-03-22 01:14:16
    ]

    for value in sample_values[:5]:
        for pattern in timestamp_patterns:
            if re.search(pattern, str(value)):
                return {'field': 'timestamp', 'confidence': 0.9}

    # Check for access result patterns
    access_results = ['granted', 'denied', 'access granted', 'access denied', 'success', 'fail']
    for value in sample_values:
        if any(result in str(value).lower() for result in access_results):
            return {'field': 'access_result', 'confidence': 0.85}

    # Check for ID patterns (letters + numbers)
    id_pattern = r'^[A-Z]\d+$|^[A-Z]+\d+$'
    id_matches = sum(1 for value in sample_values if re.match(id_pattern, str(value)))
    if id_matches >= len(sample_values) * 0.8:  # 80% match
        if 'person' in column_name.lower() or 'user' in column_name.lower():
            return {'field': 'person_id', 'confidence': 0.8}
        elif 'token' in column_name.lower() or 'badge' in column_name.lower():
            return {'field': 'token_id', 'confidence': 0.8}

    # Check for door/device patterns
    door_keywords = ['door', 'gate', 'entrance', 'exit', 'room', 'floor']
    for value in sample_values:
        if any(keyword in str(value).lower() for keyword in door_keywords):
            return {'field': 'door_id', 'confidence': 0.75}

    return {'field': '', 'confidence': 0.0}

def _get_fallback_suggestions(columns: List[str]) -> Dict[str, Dict[str, Any]]:
    """Fallback column suggestions using simple heuristics"""
    suggestions = {}
    for column in columns:
        column_lower = column.lower()
        suggestion = {'field': '', 'confidence': 0.0}
        if any(keyword in column_lower for keyword in ['person', 'user', 'employee', 'name']):
            suggestion = {'field': 'person_id', 'confidence': 0.7}
        elif any(keyword in column_lower for keyword in ['door', 'location', 'device', 'room']):
            suggestion = {'field': 'door_id', 'confidence': 0.7}
        elif any(keyword in column_lower for keyword in ['time', 'date', 'stamp']):
            suggestion = {'field': 'timestamp', 'confidence': 0.8}
        elif any(keyword in column_lower for keyword in ['result', 'status', 'access']):
            suggestion = {'field': 'access_result', 'confidence': 0.7}
        elif any(keyword in column_lower for keyword in ['token', 'badge', 'card']):
            suggestion = {'field': 'token_id', 'confidence': 0.6}
        suggestions[column] = suggestion
    return suggestions

def save_verified_mappings(filename: str, column_mappings: Dict[str, str], 
                          metadata: Dict[str, Any]) -> bool:
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
            'filename': filename,
            'file_type': filename.split('.')[-1].lower(),
            'timestamp': datetime.now().isoformat(),
            'mappings': column_mappings,
            'metadata': metadata,
            'verified_by_user': True,
            'learning_context': {
                'columns_in_file': list(column_mappings.keys()),
                'mapped_fields': list(column_mappings.values()),
                'num_columns': len(column_mappings),
                'file_size_category': metadata.get('file_size_category', 'unknown')
            }
        }

        logger.info(f"💾 Saving training data for {filename}:")
        logger.info(f"   Mappings: {column_mappings}")
        logger.info(f"   Context: {training_data['learning_context']}")

        # Try to save to AI classification plugin database
        try:
            from plugins.ai_classification.plugin import AIClassificationPlugin
            from plugins.ai_classification.config import get_ai_config

            ai_plugin = AIClassificationPlugin(get_ai_config())
            if ai_plugin.start():
                session_id = f"verified_{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

                # Store the verified mapping for AI learning
                ai_plugin.confirm_column_mapping(column_mappings, session_id)

                # Store additional training context
                if hasattr(ai_plugin, 'csv_repository'):
                    ai_plugin.csv_repository.store_column_mapping(session_id, training_data)

                logger.info(f"Verified mappings saved to AI system for {filename}")
                logger.info(f"✅ AI system updated with mappings for {filename}")

        except Exception as ai_e:
            logger.warning(f"Failed to save to AI system: {ai_e}")
            logger.info(f"AI system save failed: {ai_e}")

        # Save to file-specific training data
        try:
            import os
            os.makedirs('data/training', exist_ok=True)

            # Create file-specific training log
            today = datetime.now().strftime('%Y%m%d')
            training_file = f"data/training/column_mappings_{today}.jsonl"

            with open(training_file, 'a') as f:
                f.write(json.dumps(training_data) + '\n')

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


def register_callbacks(manager: UnifiedCallbackCoordinator) -> None:
    """Register component callbacks using the coordinator."""

    manager.register_callback(
        Output({"type": "custom-field", "index": MATCH}, "style"),
        Input({"type": "column-mapping", "index": MATCH}, "value"),
        callback_id="toggle_custom_field",
        component_name="column_verification",
    )(toggle_custom_field)


# ---------------------------------------------------------------------------
# Reversed Mapping Callbacks
# ---------------------------------------------------------------------------



__all__ = [
    'create_column_verification_modal',
    'get_ai_column_suggestions',
    'save_verified_mappings',
    'register_callbacks',
]
