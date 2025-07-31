from __future__ import annotations

"""Dash callbacks for the data enhancer service."""

import datetime
from typing import Any, Dict

import dash_bootstrap_components as dbc
import pandas as pd
from dash import Input, Output, State, callback_context, dash_table, dcc, html

from yosai_intel_dashboard.src.infrastructure.callbacks.unified_callbacks import TrulyUnifiedCallbacks

from .app import EnhancedFileProcessor, MultiBuildingDataEnhancer
from .config import (
    AI_COLUMN_SERVICE_AVAILABLE,
    AI_DOOR_SERVICE_AVAILABLE,
    CONFIG_SERVICE_AVAILABLE,
    CONTAINER_AVAILABLE,
    DoorMappingService,
    DynamicConfigurationService,
)

# Global storage for session data
session_data = {
    "uploaded_df": None,
    "column_mappings": {},
    "device_mappings": {},
    "enhanced_df": None,
    "current_step": 1,
    "building_analysis": {},
    "service_status": {
        "ai_column": AI_COLUMN_SERVICE_AVAILABLE,
        "ai_door": AI_DOOR_SERVICE_AVAILABLE,
        "config_service": CONFIG_SERVICE_AVAILABLE,
        "container": CONTAINER_AVAILABLE,
    },
}


def analyze_buildings_in_data(df: pd.DataFrame) -> Dict[str, Any]:
    """Analyze building distribution in the uploaded data."""
    analysis = {
        "total_unique_doors": 0,
        "building_distribution": {},
        "floor_distribution": {},
        "potential_buildings": [],
    }

    if "door_id" not in df.columns:
        return analysis

    unique_doors = df["door_id"].unique()
    analysis["total_unique_doors"] = len(unique_doors)

    building_types = {}
    floor_numbers = {}
    for door in unique_doors:
        door_str = str(door).lower()
        building_type = MultiBuildingDataEnhancer._detect_building_type(door_str)
        building_types[building_type] = building_types.get(building_type, 0) + 1

        floor_num = MultiBuildingDataEnhancer._detect_floor_advanced(door_str)
        floor_numbers[floor_num] = floor_numbers.get(floor_num, 0) + 1

    analysis["building_distribution"] = building_types
    analysis["floor_distribution"] = dict(sorted(floor_numbers.items()))

    potential_buildings = []
    for building_type, count in building_types.items():
        building_name = MultiBuildingDataEnhancer._generate_building_name(
            building_type, ""
        )
        potential_buildings.append(
            {"name": building_name, "type": building_type, "door_count": count}
        )

    analysis["potential_buildings"] = potential_buildings
    return analysis


def create_building_analysis_display(analysis: Dict[str, Any]) -> html.Div:
    """Create building analysis display component."""
    if not analysis or analysis["total_unique_doors"] == 0:
        return html.P("No building analysis available", className="text-muted")

    building_cards = []
    for building_info in analysis["potential_buildings"]:
        card = dbc.Card(
            [
                dbc.CardBody(
                    [
                        html.H6(building_info["name"], className="card-title"),
                        html.P(
                            f"Type: {building_info['type']}",
                            className="text-muted small",
                        ),
                        html.P(
                            f"Doors: {building_info['door_count']}",
                            className="mb-0",
                        ),
                    ]
                )
            ],
            className="mb-2",
            style={"backgroundColor": "#f8f9fa"},
        )
        building_cards.append(dbc.Col(card, width=3))

    floor_items = []
    for floor, count in analysis["floor_distribution"].items():
        floor_name = (
            f"Floor {floor}" if floor > 0 else "Basement" if floor < 0 else "Ground"
        )
        floor_items.append(html.Li(f"{floor_name}: {count} doors"))

    return html.Div(
        [
            html.H6("🏢 Multi-Building Analysis Results:"),
            html.P(
                f"Total Unique Doors: {analysis['total_unique_doors']}",
                className="mb-3",
            ),
            html.H6("Building Distribution:"),
            dbc.Row(building_cards, className="mb-3"),
            html.H6("Floor Distribution:"),
            (
                html.Ul(floor_items)
                if floor_items
                else html.P("No floor data detected", className="text-muted")
            ),
        ]
    )


def create_building_summary_report() -> str:
    """Create a comprehensive building summary report."""
    if session_data["enhanced_df"] is None:
        return "No data available for summary"

    df = session_data["enhanced_df"]
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    report = f"""
MULTI-BUILDING ACCESS CONTROL DATA ANALYSIS SUMMARY
Generated: {timestamp}
================================================

DATA OVERVIEW:
- Total Records: {len(df):,}
- Total Columns: {len(df.columns)}
- Date Range: {df['timestamp'].min() if 'timestamp' in df.columns else 'N/A'} to {df['timestamp'].max() if 'timestamp' in df.columns else 'N/A'}

"""

    if "building" in df.columns:
        building_stats = df["building"].value_counts()
        report += "BUILDING DISTRIBUTION:\n"
        for building, count in building_stats.items():
            percentage = (count / len(df)) * 100
            report += f"  {building}: {count:,} events ({percentage:.1f}%)\n"
        report += "\n"

    if "floor_number" in df.columns:
        floor_stats = df["floor_number"].value_counts().sort_index()
        report += "FLOOR DISTRIBUTION:\n"
        for floor, count in floor_stats.items():
            floor_name = (
                f"Floor {floor}"
                if floor > 0
                else "Basement" if floor < 0 else "Ground Floor"
            )
            percentage = (count / len(df)) * 100
            report += f"  {floor_name}: {count:,} events ({percentage:.1f}%)\n"
        report += "\n"

    if "security_level" in df.columns:
        security_stats = df["security_level"].value_counts().sort_index()
        report += "SECURITY LEVEL DISTRIBUTION:\n"
        for level, count in security_stats.items():
            percentage = (count / len(df)) * 100
            report += f"  Level {level}: {count:,} events ({percentage:.1f}%)\n"
        report += "\n"

    if "access_result" in df.columns:
        result_stats = df["access_result"].value_counts()
        report += "ACCESS RESULT DISTRIBUTION:\n"
        for result, count in result_stats.items():
            percentage = (count / len(df)) * 100
            report += f"  {result}: {count:,} events ({percentage:.1f}%)\n"
        report += "\n"

    if "door_id" in df.columns:
        total_doors = df["door_id"].nunique()
        most_active_doors = df["door_id"].value_counts().head(10)
        report += "DOOR ANALYSIS:\n"
        report += f"  Total Unique Doors: {total_doors}\n"
        report += "  Most Active Doors:\n"
        for door, count in most_active_doors.items():
            percentage = (count / len(df)) * 100
            report += f"    {door}: {count:,} events ({percentage:.1f}%)\n"
        report += "\n"

    special_props = [
        "is_entry",
        "is_exit",
        "is_elevator",
        "is_stairwell",
        "is_fire_escape",
        "is_restricted",
    ]
    available_props = [prop for prop in special_props if prop in df.columns]
    if available_props:
        report += "SPECIAL PROPERTIES SUMMARY:\n"
        for prop in available_props:
            count = df[df[prop] == True][prop].count() if prop in df.columns else 0
            percentage = (count / len(df)) * 100 if len(df) > 0 else 0
            prop_name = prop.replace("is_", "").replace("_", " ").title()
            report += f"  {prop_name}: {count:,} events ({percentage:.1f}%)\n"
        report += "\n"

    report += "================================================\n"
    report += "Report generated by MVP Data Enhancement Tool\n"
    return report


def register_callbacks(app, container) -> None:
    """Register Dash callbacks for ``app``."""
    callbacks = TrulyUnifiedCallbacks(app)

    @callbacks.callback(
        [
            Output("upload-status", "children"),
            Output("data-preview", "children"),
            Output("building-analysis", "children"),
            Output("progress-bar", "value"),
        ],
        [Input("upload-data", "contents")],
        [State("upload-data", "filename")],
        callback_id="handle_file_upload_enhanced",
        component_name="data_enhancer",
    )
    def handle_file_upload_enhanced(contents, filename):
        if contents is None:
            return "", "", "", 20
        df, status_msg = EnhancedFileProcessor.decode_contents(contents, filename)
        if df is None:
            status_alert = dbc.Alert(status_msg, color="danger")
            return status_alert, "", "", 20

        session_data["uploaded_df"] = df
        session_data["current_step"] = 2

        building_analysis = analyze_buildings_in_data(df)
        session_data["building_analysis"] = building_analysis

        status_alert = dbc.Alert(
            [
                html.H5("File Uploaded", className="mb-2"),
                html.P(status_msg),
            ],
            color="success",
        )
        preview_content = dash_table.DataTable(
            data=df.head().to_dict("records"),
            columns=[{"name": i, "id": i} for i in df.columns],
            style_table={"overflowX": "auto"},
            style_cell={"textAlign": "left", "padding": "10px", "fontSize": "12px"},
            style_header={
                "backgroundColor": "rgb(230, 230, 230)",
                "fontWeight": "bold",
            },
        )
        building_content = create_building_analysis_display(building_analysis)
        return status_alert, preview_content, building_content, 40

    @callbacks.callback(
        [
            Output("column-mapping-controls", "children"),
            Output("ai-column-status", "children"),
        ],
        [Input("ai-column-btn", "n_clicks")],
        callback_id="handle_enhanced_column_mapping",
        component_name="data_enhancer",
    )
    def handle_enhanced_column_mapping(n_clicks):
        if session_data["uploaded_df"] is None:
            return "", dbc.Alert("Please upload a file first", color="warning")

        df = session_data["uploaded_df"]
        if n_clicks:
            try:
                suggestions = MultiBuildingDataEnhancer.get_enhanced_column_suggestions(
                    df
                )
                status_msg = f"Enhanced AI suggestions generated ({len(suggestions)} matches found)"
                if not AI_COLUMN_SERVICE_AVAILABLE:
                    status_msg += " (Using enhanced fallback service)"
                ai_status = dbc.Alert(status_msg, color="info")
            except Exception as e:  # pragma: no cover - best effort
                suggestions = {}
                ai_status = dbc.Alert(f"AI service error: {str(e)}", color="warning")
        else:
            suggestions = {}
            ai_status = ""

        controls = []
        for field in MultiBuildingDataEnhancer.STANDARD_FIELDS:
            suggested_col = suggestions.get(field, {}).get("suggested_column", "None")
            confidence = suggestions.get(field, {}).get("confidence", 0)

            options = [{"label": "None", "value": "None"}] + [
                {"label": col, "value": col} for col in df.columns
            ]

            label_text = field
            if confidence > 0:
                label_text += f" (AI: {confidence:.1%} confidence)"

            label_class = "font-weight-bold"
            if field in ["facility_id", "building_id", "zone_id", "floor"]:
                label_class += " text-primary"

            control = dbc.Row(
                [
                    dbc.Col([dbc.Label(label_text, className=label_class)], width=4),
                    dbc.Col(
                        [
                            dcc.Dropdown(
                                id=f"mapping-{field}",
                                options=options,
                                value=suggested_col,
                                placeholder=f"Select column for {field}",
                            )
                        ],
                        width=8,
                    ),
                ],
                className="mb-2",
            )
            controls.append(control)

        return controls, ai_status

    @callbacks.callback(
        [
            Output("device-mapping-controls", "children"),
            Output("ai-device-status", "children"),
            Output("building-types-summary", "children"),
        ],
        [Input("ai-device-btn", "n_clicks")],
        callback_id="handle_enhanced_device_mapping",
        component_name="data_enhancer",
    )
    def handle_enhanced_device_mapping(n_clicks):
        if session_data["uploaded_df"] is None:
            return "", dbc.Alert("Please upload a file first", color="warning"), ""

        df = session_data["uploaded_df"]
        if "door_id" not in df.columns:
            return (
                "",
                dbc.Alert(
                    "No 'door_id' column found for device mapping", color="warning"
                ),
                "",
            )

        if n_clicks:
            try:
                suggestions = MultiBuildingDataEnhancer.get_enhanced_device_suggestions(
                    df
                )
                status_msg = f"Enhanced AI device suggestions generated for {len(suggestions)} devices"
                if not AI_DOOR_SERVICE_AVAILABLE:
                    status_msg += " (Using enhanced fallback service)"
                ai_status = dbc.Alert(status_msg, color="info")
                session_data["device_mappings"] = suggestions
            except Exception as e:  # pragma: no cover - best effort
                suggestions = {}
                ai_status = dbc.Alert(
                    f"AI device service error: {str(e)}", color="warning"
                )
        else:
            suggestions = session_data.get("device_mappings", {})
            ai_status = ""

        building_types = {}
        for device_data in suggestions.values():
            building_type = device_data.get("building_type", "unknown")
            building_types[building_type] = building_types.get(building_type, 0) + 1

        building_summary = []
        for building_type, count in building_types.items():
            badge_color = "primary" if building_type == "main" else "secondary"
            building_summary.append(
                dbc.Badge(
                    f"{building_type.title()}: {count}",
                    color=badge_color,
                    className="me-2 mb-1",
                )
            )

        unique_doors = df["door_id"].unique()[:15]
        controls = []
        for door_id in unique_doors:
            door_data = suggestions.get(str(door_id), {})
            door_card = dbc.Card(
                [
                    dbc.CardHeader(
                        [
                            html.H6(f"Door ID: {door_id}", className="mb-0"),
                            html.Small(
                                f"Building: {door_data.get('building', 'Unknown')}",
                                className="text-muted",
                            ),
                        ]
                    ),
                    dbc.CardBody(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            dbc.Label("Building Name:"),
                                            dbc.Input(
                                                id=f"building-{door_id}",
                                                value=door_data.get(
                                                    "building", "Main Building"
                                                ),
                                                placeholder="Building name",
                                            ),
                                        ],
                                        width=6,
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.Label("Building Type:"),
                                            dcc.Dropdown(
                                                id=f"building-type-{door_id}",
                                                options=[
                                                    {
                                                        "label": "Main Building",
                                                        "value": "main",
                                                    },
                                                    {
                                                        "label": "North Wing",
                                                        "value": "north",
                                                    },
                                                    {
                                                        "label": "South Wing",
                                                        "value": "south",
                                                    },
                                                    {
                                                        "label": "East Wing",
                                                        "value": "east",
                                                    },
                                                    {
                                                        "label": "West Wing",
                                                        "value": "west",
                                                    },
                                                    {
                                                        "label": "Annex Building",
                                                        "value": "annex",
                                                    },
                                                    {
                                                        "label": "Tower Building",
                                                        "value": "tower",
                                                    },
                                                ],
                                                value=door_data.get(
                                                    "building_type", "main"
                                                ),
                                            ),
                                        ],
                                        width=6,
                                    ),
                                ],
                                className="mb-2",
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            dbc.Label("Floor Number (-5 to 100):"),
                                            dbc.Input(
                                                id=f"floor-{door_id}",
                                                type="number",
                                                min=-5,
                                                max=100,
                                                value=door_data.get("floor_number", 1),
                                            ),
                                        ],
                                        width=6,
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.Label("Security Level (1-10):"),
                                            dbc.Input(
                                                id=f"security-{door_id}",
                                                type="number",
                                                min=1,
                                                max=10,
                                                value=door_data.get(
                                                    "security_level", 5
                                                ),
                                            ),
                                        ],
                                        width=6,
                                    ),
                                ],
                                className="mb-2",
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            dbc.Label("Access Types:"),
                                            dbc.Checklist(
                                                id=f"access-{door_id}",
                                                options=[
                                                    {
                                                        "label": "Entry Point",
                                                        "value": "is_entry",
                                                    },
                                                    {
                                                        "label": "Exit Point",
                                                        "value": "is_exit",
                                                    },
                                                ],
                                                value=[
                                                    k
                                                    for k, v in door_data.items()
                                                    if k in ["is_entry", "is_exit"]
                                                    and v
                                                ],
                                                inline=True,
                                            ),
                                        ],
                                        width=6,
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.Label("Special Properties:"),
                                            dbc.Checklist(
                                                id=f"special-{door_id}",
                                                options=[
                                                    {
                                                        "label": "Elevator",
                                                        "value": "is_elevator",
                                                    },
                                                    {
                                                        "label": "Stairwell",
                                                        "value": "is_stairwell",
                                                    },
                                                    {
                                                        "label": "Fire Exit",
                                                        "value": "is_fire_escape",
                                                    },
                                                    {
                                                        "label": "Restricted",
                                                        "value": "is_restricted",
                                                    },
                                                ],
                                                value=[
                                                    k
                                                    for k, v in door_data.items()
                                                    if k.startswith("is_")
                                                    and k not in ["is_entry", "is_exit"]
                                                    and v
                                                ],
                                                inline=True,
                                            ),
                                        ],
                                        width=6,
                                    ),
                                ]
                            ),
                        ]
                    ),
                ],
                className="mb-3",
            )
            controls.append(door_card)

        return controls, ai_status, building_summary

    @callbacks.callback(
        [
            Output("enhancement-status", "children"),
            Output("enhanced-preview", "children"),
            Output("progress-bar", "value", allow_duplicate=True),
        ],
        [Input("enhance-btn", "n_clicks")],
        [
            State(f"mapping-{field}", "value")
            for field in MultiBuildingDataEnhancer.STANDARD_FIELDS
        ],
        prevent_initial_call=True,
        callback_id="handle_enhanced_data_enhancement",
        component_name="data_enhancer",
    )
    def handle_enhanced_data_enhancement(n_clicks, *mapping_values):
        if not n_clicks or session_data["uploaded_df"] is None:
            return "", "", 80
        try:
            df = session_data["uploaded_df"].copy()
            column_mappings = {}
            for i, field in enumerate(MultiBuildingDataEnhancer.STANDARD_FIELDS):
                if mapping_values[i] and mapping_values[i] != "None":
                    column_mappings[field] = mapping_values[i]

            enhanced_df = MultiBuildingDataEnhancer.apply_column_mappings(
                df, column_mappings
            )
            enhanced_df = MultiBuildingDataEnhancer.apply_device_mappings(
                enhanced_df, session_data.get("device_mappings", {})
            )

            session_data["enhanced_df"] = enhanced_df
            session_data["column_mappings"] = column_mappings
            session_data["current_step"] = 6

            original_cols = len(df.columns)
            enhanced_cols = len(enhanced_df.columns)
            new_cols = enhanced_cols - original_cols

            building_count = (
                len(enhanced_df["building"].unique())
                if "building" in enhanced_df.columns
                else 0
            )
            floor_count = (
                len(enhanced_df["floor_number"].unique())
                if "floor_number" in enhanced_df.columns
                else 0
            )

            status = dbc.Alert(
                [
                    html.H5(
                        "Multi-Building Data Enhancement Complete!", className="mb-2"
                    ),
                    html.P(f"Original columns: {original_cols}"),
                    html.P(f"Enhanced columns: {enhanced_cols}"),
                    html.P(f"New columns added: {new_cols}"),
                    html.P(f"Column mappings applied: {len(column_mappings)}"),
                    html.P(f"Buildings detected: {building_count}"),
                    html.P(f"Floors detected: {floor_count}"),
                ],
                color="success",
            )

            preview_cols = list(enhanced_df.columns)
            original_cols_list = list(df.columns)
            style_data_conditional = []
            for col in preview_cols:
                if col not in original_cols_list:
                    if col in ["building", "building_type", "floor_number"]:
                        style_data_conditional.append(
                            {
                                "if": {"column_id": col},
                                "backgroundColor": "#e3f2fd",
                                "color": "black",
                                "fontWeight": "bold",
                            }
                        )
                    else:
                        style_data_conditional.append(
                            {
                                "if": {"column_id": col},
                                "backgroundColor": "#e8f5e8",
                                "color": "black",
                                "fontWeight": "bold",
                            }
                        )

            preview = [
                html.H6("Enhanced Multi-Building Data Preview (First 5 Rows):"),
                html.P(
                    "Building columns are highlighted in blue, other new columns in green",
                    className="text-muted small",
                ),
                dash_table.DataTable(
                    data=enhanced_df.head().to_dict("records"),
                    columns=[{"name": i, "id": i} for i in enhanced_df.columns],
                    style_table={"overflowX": "auto"},
                    style_cell={
                        "textAlign": "left",
                        "padding": "10px",
                        "fontSize": "12px",
                    },
                    style_header={
                        "backgroundColor": "rgb(230, 230, 230)",
                        "fontWeight": "bold",
                    },
                    style_data_conditional=style_data_conditional,
                ),
            ]
            return status, preview, 100
        except Exception as e:  # pragma: no cover - best effort
            error_msg = dbc.Alert(f"Enhancement error: {str(e)}", color="danger")
            return error_msg, "", 80

    @callbacks.callback(
        [
            Output("download-csv", "data"),
            Output("download-json", "data"),
            Output("download-summary", "data"),
        ],
        [
            Input("download-csv-btn", "n_clicks"),
            Input("download-json-btn", "n_clicks"),
            Input("download-summary-btn", "n_clicks"),
        ],
        prevent_initial_call=True,
        callback_id="handle_enhanced_downloads",
        component_name="data_enhancer",
    )
    def handle_enhanced_downloads(csv_clicks, json_clicks, summary_clicks):
        if session_data["enhanced_df"] is None:
            return None, None, None

        ctx = callback_context
        if not ctx.triggered:
            return None, None, None

        button_id = ctx.triggered[0]["prop_id"].split(".")[0]
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        if button_id == "download-csv-btn" and csv_clicks:
            return (
                dcc.send_data_frame(
                    session_data["enhanced_df"].to_csv,
                    f"enhanced_multi_building_data_{timestamp}.csv",
                    index=False,
                ),
                None,
                None,
            )
        elif button_id == "download-json-btn" and json_clicks:
            return (
                None,
                dcc.send_data_frame(
                    session_data["enhanced_df"].to_json,
                    f"enhanced_multi_building_data_{timestamp}.json",
                    orient="records",
                ),
                None,
            )
        elif button_id == "download-summary-btn" and summary_clicks:
            summary_data = create_building_summary_report()
            return (
                None,
                None,
                dict(
                    content=summary_data,
                    filename=f"building_analysis_summary_{timestamp}.txt",
                ),
            )
        return None, None, None
