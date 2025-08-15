from __future__ import annotations

import datetime
from typing import Any, Dict, Tuple

import dash_bootstrap_components as dbc
import pandas as pd
from dash import html

from .config import (
    AI_COLUMN_SERVICE_AVAILABLE,
    AI_DOOR_SERVICE_AVAILABLE,
    CONFIG_SERVICE_AVAILABLE,
    CONTAINER_AVAILABLE,
)

# Shared session storage for data enhancer callbacks
session_data: Dict[str, Any] = {
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
    from .app import MultiBuildingDataEnhancer

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

    building_types: Dict[str, int] = {}
    floor_numbers: Dict[int, int] = {}
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


def process_uploaded_file(
    contents: str | None, filename: str | None
) -> Tuple[pd.DataFrame | None, str, Dict[str, Any]]:
    """Decode uploaded file and prepare building analysis."""
    if contents is None:
        return None, "", {}

    from .app import EnhancedFileProcessor

    df, status_msg = EnhancedFileProcessor.decode_contents(contents, filename)
    if df is None:
        return None, status_msg, {}

    session_data["uploaded_df"] = df
    session_data["current_step"] = 2

    building_analysis = analyze_buildings_in_data(df)
    session_data["building_analysis"] = building_analysis
    return df, status_msg, building_analysis


def create_building_summary_report() -> str:
    """Create a comprehensive building summary report."""
    if session_data["enhanced_df"] is None:
        return "No data available for summary"

    df = session_data["enhanced_df"]
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    report_lines = [
        f"""
MULTI-BUILDING ACCESS CONTROL DATA ANALYSIS SUMMARY
Generated: {timestamp}
================================================

DATA OVERVIEW:
- Total Records: {len(df):,}
- Total Columns: {len(df.columns)}
- Date Range: {df['timestamp'].min() if 'timestamp' in df.columns else 'N/A'} to {df['timestamp'].max() if 'timestamp' in df.columns else 'N/A'}

""",
    ]

    if "building" in df.columns:
        building_stats = df["building"].value_counts()
        report_lines.append("BUILDING DISTRIBUTION:\n")
        for building, count in building_stats.items():
            percentage = (count / len(df)) * 100
            report_lines.append(
                f"  {building}: {count:,} events ({percentage:.1f}%)\n"
            )
        report_lines.append("\n")

    if "floor_number" in df.columns:
        floor_stats = df["floor_number"].value_counts().sort_index()
        report_lines.append("FLOOR DISTRIBUTION:\n")
        for floor, count in floor_stats.items():
            floor_name = (
                f"Floor {floor}"
                if floor > 0
                else "Basement" if floor < 0 else "Ground Floor"
            )
            percentage = (count / len(df)) * 100
            report_lines.append(
                f"  {floor_name}: {count:,} events ({percentage:.1f}%)\n"
            )
        report_lines.append("\n")

    if "security_level" in df.columns:
        security_stats = df["security_level"].value_counts().sort_index()
        report_lines.append("SECURITY LEVEL DISTRIBUTION:\n")
        for level, count in security_stats.items():
            percentage = (count / len(df)) * 100
            report_lines.append(
                f"  Level {level}: {count:,} events ({percentage:.1f}%)\n"
            )
        report_lines.append("\n")

    if "access_result" in df.columns:
        result_stats = df["access_result"].value_counts()
        report_lines.append("ACCESS RESULT DISTRIBUTION:\n")
        for result, count in result_stats.items():
            percentage = (count / len(df)) * 100
            report_lines.append(
                f"  {result}: {count:,} events ({percentage:.1f}%)\n"
            )
        report_lines.append("\n")

    if "door_id" in df.columns:
        total_doors = df["door_id"].nunique()
        most_active_doors = df["door_id"].value_counts().head(10)
        report_lines.append("DOOR ANALYSIS:\n")
        report_lines.append(f"  Total Unique Doors: {total_doors}\n")
        report_lines.append("  Most Active Doors:\n")
        for door, count in most_active_doors.items():
            percentage = (count / len(df)) * 100
            report_lines.append(
                f"    {door}: {count:,} events ({percentage:.1f}%)\n"
            )
        report_lines.append("\n")

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
        report_lines.append("SPECIAL PROPERTIES SUMMARY:\n")
        for prop in available_props:
            count = df[df[prop] == True][prop].count() if prop in df.columns else 0
            percentage = (count / len(df)) * 100 if len(df) > 0 else 0
            prop_name = prop.replace("is_", "").replace("_", " ").title()
            report_lines.append(
                f"  {prop_name}: {count:,} events ({percentage:.1f}%)\n"
            )
        report_lines.append("\n")

    report_lines.append("================================================\n")
    report_lines.append("Report generated by MVP Data Enhancement Tool\n")
    return "".join(report_lines)
