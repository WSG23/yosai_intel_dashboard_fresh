#!/usr/bin/env python3
from __future__ import annotations

"""Dash application for the MVP data enhancer."""

import base64
import datetime
import io
import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import dash
import dash_bootstrap_components as dbc
import pandas as pd
from dash import dcc, html

from config.constants import DEFAULT_CHUNK_SIZE
from core.unicode import clean_unicode_surrogates

from .config import (
    AI_COLUMN_SERVICE_AVAILABLE,
    AI_DOOR_SERVICE_AVAILABLE,
    CONFIG_SERVICE_AVAILABLE,
    CONTAINER_AVAILABLE,
    DoorMappingService,
    DynamicConfigurationService,
)

if CONTAINER_AVAILABLE:
    from core.service_container import ServiceContainer

PROJECT_ROOT = Path(__file__).resolve().parents[2]

logger = logging.getLogger(__name__)


class AdvancedUnicodeHandler:
    """Enhanced Unicode handling with building-specific character support"""

    @staticmethod
    def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """Clean entire dataframe of Unicode issues"""
        cleaned_df = df.copy()

        # Clean column names
        cleaned_df.columns = [
            clean_unicode_surrogates(str(col)) for col in cleaned_df.columns
        ]

        # Clean string columns
        for col in cleaned_df.columns:
            if cleaned_df[col].dtype == "object":
                cleaned_df[col] = (
                    cleaned_df[col].astype(str).apply(clean_unicode_surrogates)
                )

        return cleaned_df


class EnhancedFileProcessor:
    """Advanced file processor with multi-building file format support"""

    ENCODINGS = [
        "utf-8",
        "latin1",
        "cp1252",
        "iso-8859-1",
        "utf-16",
        "shift_jis",
        "euc-jp",
    ]

    @staticmethod
    def decode_contents(
        contents: str, filename: str
    ) -> Tuple[Optional[pd.DataFrame], str]:
        """Decode uploaded file contents with multiple encoding attempts"""
        try:
            # Parse the base64 encoded file
            content_type, content_string = contents.split(",")
            decoded = base64.b64decode(content_string)

            # Try different encodings
            for encoding in EnhancedFileProcessor.ENCODINGS:
                try:
                    if filename.endswith(".csv"):
                        df = pd.read_csv(io.StringIO(decoded.decode(encoding)))
                    elif filename.endswith(".json"):
                        data = json.loads(decoded.decode(encoding))
                        df = (
                            pd.json_normalize(data)
                            if isinstance(data, list)
                            else pd.DataFrame([data])
                        )
                    elif filename.endswith((".xls", ".xlsx")):
                        df = pd.read_excel(io.BytesIO(decoded))
                    else:
                        return None, f"Unsupported file type: {filename}"

                    # Clean Unicode issues
                    df = AdvancedUnicodeHandler.clean_dataframe(df)

                    return df, f"Successfully loaded with {encoding} encoding"

                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    logger.error(f"Error with {encoding}: {str(e)}")
                    continue

            return None, "Could not decode file with any supported encoding"

        except Exception as e:
            logger.error(f"File processing error: {str(e)}")
            return None, f"Error processing file: {str(e)}"


class MultiBuildingDataEnhancer:
    """Enhanced data enhancer with multi-building and annex support"""

    # Enhanced standard fields including building/facility support
    STANDARD_FIELDS = [
        "person_id",
        "door_id",
        "access_result",
        "timestamp",
        "token_id",
        "event_type",
        "facility_id",
        "building_id",
        "zone_id",
        "floor",
        "direction",
    ]

    # Building detection patterns (based on latest GitHub updates)
    BUILDING_PATTERNS = {
        "main": ["main", "primary", "central", "headquarters", "hq"],
        "north": ["north", "n_", "_n", "northern", "bldg_n"],
        "south": ["south", "s_", "_s", "southern", "bldg_s"],
        "east": ["east", "e_", "_e", "eastern", "bldg_e"],
        "west": ["west", "w_", "_w", "western", "bldg_w"],
        "annex": ["annex", "auxiliary", "secondary", "extension", "wing"],
        "tower": ["tower", "high_rise", "vertical", "tall"],
    }

    # Enhanced floor detection patterns (from latest code)
    FLOOR_PATTERNS = [
        r"\b(\d+)(?:st|nd|rd|th)?\s*fl(?:oor)?\b",  # "2nd floor", "3 fl"
        r"\bfl(?:oor)?\s*(\d+)\b",  # "floor 2", "fl 3"
        r"\blevel[\s\-_]*(\d+)\b",  # "level 2", "level-3"
        r"\bf(\d+)\b",  # "f2", "f10", "f03", "f04"
        r"\b(\d+)f\b",  # "2f", "10f"
        r"\b(\d+)-\d+\b",  # "2-101" (floor-room)
        r"\b(\d+)\.\d+\b",  # "2.101" (floor.room)
        r"\b(\d+)_\d+\b",  # "2_101" (floor_room)
        r"\bf0*(\d+)\b",  # "f01", "f03", "f004" (zero-padded)
        r"\b(\d+)(?=\d{2,3})\b",  # "301" -> "3", "1205" -> "12"
    ]

    @staticmethod
    def get_enhanced_column_suggestions(df: pd.DataFrame) -> Dict[str, Dict]:
        """Enhanced AI column suggestions with multi-building support"""

        # Try existing service first
        if AI_COLUMN_SERVICE_AVAILABLE:
            try:
                from services.data_enhancer.mapping_utils import (
                    get_ai_column_suggestions,
                )

                return get_ai_column_suggestions(
                    df, MultiBuildingDataEnhancer.STANDARD_FIELDS
                )
            except Exception as e:
                logger.warning(f"AI service error: {e}")

        # Enhanced fallback with building-aware mapping
        suggestions = {}
        df_columns = list(df.columns)

        # Enhanced field keywords including building/facility fields
        field_keywords = {
            "person_id": ["person", "user", "employee", "staff", "id", "emp", "badge"],
            "door_id": [
                "door",
                "entrance",
                "exit",
                "gate",
                "portal",
                "device",
                "reader",
            ],
            "access_result": [
                "result",
                "status",
                "outcome",
                "success",
                "granted",
                "decision",
            ],
            "timestamp": ["time", "date", "when", "occurred", "stamp", "datetime"],
            "token_id": ["token", "card", "badge", "key", "access", "credential"],
            "event_type": ["event", "type", "action", "activity", "category"],
            "facility_id": ["facility", "building", "bldg", "structure", "complex"],
            "building_id": ["building", "bldg", "tower", "wing", "annex", "block"],
            "zone_id": ["zone", "area", "sector", "region", "district"],
            "floor": ["floor", "level", "storey", "fl", "lvl"],
            "direction": ["direction", "entry_exit", "in_out", "flow"],
        }

        for field in MultiBuildingDataEnhancer.STANDARD_FIELDS:
            keywords = field_keywords.get(field, [field.replace("_", "")])
            for col in df_columns:
                col_lower = col.lower()
                for keyword in keywords:
                    if keyword in col_lower:
                        suggestions[field] = {
                            "suggested_column": col,
                            "confidence": 0.85,
                            "reason": f'Enhanced pattern match: "{keyword}" in column "{col}"',
                        }
                        break
                if field in suggestions:
                    break

        return suggestions

    @staticmethod
    def get_enhanced_device_suggestions(df: pd.DataFrame) -> Dict[str, Dict]:
        """Enhanced device suggestions with multi-building analysis"""

        # Try existing service first
        if AI_DOOR_SERVICE_AVAILABLE:
            try:
                # Try to create proper config for the service
                config = (
                    DynamicConfigurationService() if CONFIG_SERVICE_AVAILABLE else None
                )

                # Try to use the real service
                door_service = DoorMappingService(config)
                result = door_service.process_uploaded_data(df)
                return result.get("device_suggestions", {})
            except Exception as e:
                logger.warning(f"Door service error: {e}")

        # Enhanced fallback with multi-building support
        suggestions = {}

        if "door_id" not in df.columns:
            return suggestions

        unique_doors = df["door_id"].unique()[:20]  # Increased limit for multi-building

        for door in unique_doors:
            door_str = str(door).lower()

            # Enhanced building detection
            building_type = MultiBuildingDataEnhancer._detect_building_type(door_str)
            building_name = MultiBuildingDataEnhancer._generate_building_name(
                building_type, door_str
            )

            # Enhanced floor detection
            floor_number = MultiBuildingDataEnhancer._detect_floor_advanced(door_str)

            # Enhanced security level based on building type and location
            security_level = MultiBuildingDataEnhancer._calculate_security_level(
                door_str, building_type, floor_number
            )

            # Enhanced access type detection
            access_types = MultiBuildingDataEnhancer._detect_access_types(door_str)

            # Enhanced special properties detection
            special_props = MultiBuildingDataEnhancer._detect_special_properties(
                door_str
            )

            suggestions[str(door)] = {
                "building": building_name,
                "building_type": building_type,
                "floor_number": floor_number,
                "security_level": security_level,
                **access_types,
                **special_props,
                "confidence": 0.8,
            }

        return suggestions

    @staticmethod
    def _detect_building_type(door_str: str) -> str:
        """Detect building type from door identifier"""
        for (
            building_type,
            patterns,
        ) in MultiBuildingDataEnhancer.BUILDING_PATTERNS.items():
            for pattern in patterns:
                if pattern in door_str:
                    return building_type
        return "main"

    @staticmethod
    def _generate_building_name(building_type: str, door_str: str) -> str:
        """Generate human-readable building name"""
        building_names = {
            "main": "Main Building",
            "north": "North Wing",
            "south": "South Wing",
            "east": "East Wing",
            "west": "West Wing",
            "annex": "Annex Building",
            "tower": "Tower Building",
        }

        # Look for specific building indicators
        if "tower" in door_str:
            if any(x in door_str for x in ["1", "a", "first"]):
                return "Tower A"
            elif any(x in door_str for x in ["2", "b", "second"]):
                return "Tower B"
            return "Tower Building"

        return building_names.get(building_type, "Main Building")

    @staticmethod
    def _detect_floor_advanced(door_str: str) -> int:
        """Advanced floor detection with zero-padding support"""
        for pattern in MultiBuildingDataEnhancer.FLOOR_PATTERNS:
            matches = re.finditer(pattern, door_str, re.IGNORECASE)
            for match in matches:
                try:
                    floor_num = int(match.group(1))
                    # Handle zero-padded numbers like F03 -> floor 3
                    if "f0" in door_str.lower() and floor_num < 10:
                        return floor_num
                    # Standard range check
                    if 1 <= floor_num <= 100:
                        return floor_num
                except (ValueError, IndexError):
                    continue

        # Basement detection
        if any(x in door_str for x in ["basement", "b1", "b2", "underground", "sub"]):
            return -1

        return 1  # Default to ground floor

    @staticmethod
    def _calculate_security_level(
        door_str: str, building_type: str, floor_number: int
    ) -> int:
        """Calculate security level based on building context"""
        base_security = 5

        # Building type adjustments
        building_security_modifiers = {
            "main": 0,
            "annex": -1,
            "tower": +2,
            "north": +1,
            "south": +1,
            "east": 0,
            "west": 0,
        }

        security_level = base_security + building_security_modifiers.get(
            building_type, 0
        )

        # Floor-based adjustments
        if floor_number < 0:  # Basement
            security_level += 3
        elif floor_number > 10:  # High floors
            security_level += 2

        # Area-specific adjustments
        high_security_areas = [
            "server",
            "data",
            "executive",
            "ceo",
            "finance",
            "secure",
            "restricted",
        ]
        medium_security_areas = ["office", "meeting", "conference"]
        low_security_areas = ["lobby", "entrance", "public", "visitor", "cafeteria"]

        for area in high_security_areas:
            if area in door_str:
                security_level += 4
                break

        for area in medium_security_areas:
            if area in door_str:
                security_level += 1
                break

        for area in low_security_areas:
            if area in door_str:
                security_level -= 2
                break

        return max(1, min(10, security_level))

    @staticmethod
    def _detect_access_types(door_str: str) -> Dict[str, bool]:
        """Detect access types (entry/exit)"""
        return {
            "is_entry": any(
                x in door_str for x in ["entry", "entrance", "main", "front", "in"]
            ),
            "is_exit": any(x in door_str for x in ["exit", "emergency", "back", "out"]),
        }

    @staticmethod
    def _detect_special_properties(door_str: str) -> Dict[str, bool]:
        """Detect special properties (elevator, stairwell, etc.)"""
        return {
            "is_elevator": any(x in door_str for x in ["elevator", "lift", "elev"]),
            "is_stairwell": any(
                x in door_str for x in ["stair", "stairs", "stairwell"]
            ),
            "is_fire_escape": any(
                x in door_str for x in ["fire", "emergency", "escape"]
            ),
            "is_restricted": any(
                x in door_str for x in ["restricted", "secure", "private", "authorized"]
            ),
        }

    @staticmethod
    def apply_column_mappings(
        df: pd.DataFrame, mappings: Dict[str, str]
    ) -> pd.DataFrame:
        """Apply column mappings to rename fields"""
        enhanced_df = df.copy()
        rename_map = {v: k for k, v in mappings.items() if v and v != "None"}

        if rename_map:
            enhanced_df = enhanced_df.rename(columns=rename_map)

        return enhanced_df

    @staticmethod
    def apply_device_mappings(
        df: pd.DataFrame, device_mappings: Dict[str, Dict]
    ) -> pd.DataFrame:
        """Apply device mappings to add comprehensive metadata columns"""
        enhanced_df = df.copy()

        if not device_mappings or "door_id" not in enhanced_df.columns:
            return enhanced_df

        # Enhanced new columns including building/facility data
        new_columns = {
            "building": "Unknown Building",
            "building_type": "main",
            "floor_number": 1,
            "security_level": 5,
            "is_entry": False,
            "is_exit": False,
            "is_elevator": False,
            "is_stairwell": False,
            "is_fire_escape": False,
            "is_restricted": False,
        }

        for col, default_val in new_columns.items():
            enhanced_df[col] = default_val

        # Apply device-specific mappings
        for door_id, mappings in device_mappings.items():
            mask = enhanced_df["door_id"].astype(str) == str(door_id)
            for col, value in mappings.items():
                if col in new_columns:
                    enhanced_df.loc[mask, col] = value

        return enhanced_df


# Custom CSS styling with enhanced visual design
CUSTOM_STYLE = {
    "background": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
    "minHeight": "100vh",
    "padding": "20px",
}

CARD_STYLE = {
    "margin": "10px 0",
    "boxShadow": "0 6px 12px rgba(0, 0, 0, 0.15)",
    "borderRadius": "15px",
    "border": "1px solid rgba(255, 255, 255, 0.1)",
}

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


def create_enhanced_header():
    """Create enhanced header with service status and building analysis info"""

    service_badges = []

    if AI_COLUMN_SERVICE_AVAILABLE:
        service_badges.append(
            dbc.Badge("AI Column ✅", color="success", className="me-2")
        )
    else:
        service_badges.append(
            dbc.Badge("AI Column ⚠️", color="warning", className="me-2")
        )

    if AI_DOOR_SERVICE_AVAILABLE:
        service_badges.append(
            dbc.Badge("AI Door ✅", color="success", className="me-2")
        )
    else:
        service_badges.append(dbc.Badge("AI Door ⚠️", color="warning", className="me-2"))

    if CONFIG_SERVICE_AVAILABLE:
        service_badges.append(dbc.Badge("Config ✅", color="success", className="me-2"))
    else:
        service_badges.append(dbc.Badge("Config ⚠️", color="warning", className="me-2"))

    if CONTAINER_AVAILABLE:
        service_badges.append(
            dbc.Badge("Services ✅", color="success", className="me-2")
        )
    else:
        service_badges.append(
            dbc.Badge("Services ⚠️", color="warning", className="me-2")
        )

    # Add multi-building badge
    service_badges.append(
        dbc.Badge("Multi-Building 🏢", color="info", className="me-2")
    )

    return dbc.Card(
        [
            dbc.CardBody(
                [
                    html.H1(
                        "MVP Data Enhancement Tool",
                        className="text-center text-primary mb-2",
                    ),
                    html.P(
                        "Advanced Multi-Building Analysis - Core Testing",
                        className="text-center text-muted mb-3",
                    ),
                    html.Div(service_badges, className="text-center mb-3"),
                    html.P(
                        "Upload, map, enhance, and export multi-building access control data",
                        className="text-center text-muted mb-4",
                    ),
                    dbc.Progress(
                        id="progress-bar", value=20, striped=True, animated=True
                    ),
                ]
            )
        ],
        style=CARD_STYLE,
    )


def create_upload_section():
    """Create enhanced file upload section"""
    return dbc.Card(
        [
            dbc.CardHeader(
                html.H4(
                    "Step 1: File Upload & Multi-Building Detection", className="mb-0"
                )
            ),
            dbc.CardBody(
                [
                    dcc.Upload(
                        id="upload-data",
                        children=html.Div(
                            [
                                html.I(className="fas fa-cloud-upload-alt fa-3x mb-3"),
                                html.H5("Drag & Drop or Click to Upload"),
                                html.P("Supports CSV, JSON, XLS, XLSX files"),
                                html.P(
                                    "Enhanced encoding support + building detection",
                                    className="text-muted small",
                                ),
                            ],
                            className="text-center",
                        ),
                        style={
                            "width": "100%",
                            "height": "140px",
                            "lineHeight": "140px",
                            "borderWidth": "3px",
                            "borderStyle": "dashed",
                            "borderRadius": "15px",
                            "borderColor": "#cccccc",
                            "textAlign": "center",
                            "backgroundColor": "#fafafa",
                        },
                        multiple=False,
                    ),
                    html.Div(id="upload-status", className="mt-3"),
                ]
            ),
        ],
        style=CARD_STYLE,
    )


def create_preview_section():
    """Create enhanced data preview section"""
    return dbc.Card(
        [
            dbc.CardHeader(
                html.H4("Step 2: Data Preview & Building Analysis", className="mb-0")
            ),
            dbc.CardBody(
                [
                    html.Div(id="data-preview"),
                    html.Hr(),
                    html.Div(id="building-analysis"),
                ]
            ),
        ],
        style=CARD_STYLE,
    )


def create_column_mapping_section():
    """Create enhanced column mapping section"""
    return dbc.Card(
        [
            dbc.CardHeader(
                html.H4("Step 3: Enhanced Column Mapping", className="mb-0")
            ),
            dbc.CardBody(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Button(
                                        "Get AI Suggestions",
                                        id="ai-column-btn",
                                        color="primary",
                                        className="mb-3",
                                    ),
                                    html.Div(id="ai-column-status"),
                                ],
                                width=6,
                            ),
                            dbc.Col(
                                [
                                    html.P(
                                        "Enhanced Standard Fields:",
                                        className="font-weight-bold",
                                    ),
                                    html.Ul(
                                        [
                                            html.Li(field)
                                            for field in MultiBuildingDataEnhancer.STANDARD_FIELDS
                                        ]
                                    ),
                                ],
                                width=6,
                            ),
                        ]
                    ),
                    html.Hr(),
                    html.Div(id="column-mapping-controls"),
                ]
            ),
        ],
        style=CARD_STYLE,
    )


def create_device_mapping_section():
    """Create enhanced device mapping section with building context"""
    return dbc.Card(
        [
            dbc.CardHeader(
                html.H4("Step 4: Multi-Building Device Mapping", className="mb-0")
            ),
            dbc.CardBody(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Button(
                                        "Get AI Device Suggestions",
                                        id="ai-device-btn",
                                        color="success",
                                        className="mb-3",
                                    ),
                                    html.Div(id="ai-device-status"),
                                ],
                                width=6,
                            ),
                            dbc.Col(
                                [
                                    html.P(
                                        "Building Types Detected:",
                                        className="font-weight-bold",
                                    ),
                                    html.Div(id="building-types-summary"),
                                ],
                                width=6,
                            ),
                        ]
                    ),
                    html.Hr(),
                    html.Div(id="device-mapping-controls"),
                ]
            ),
        ],
        style=CARD_STYLE,
    )


def create_enhancement_section():
    """Create enhanced data enhancement section"""
    return dbc.Card(
        [
            dbc.CardHeader(
                html.H4("Step 5: Multi-Building Data Enhancement", className="mb-0")
            ),
            dbc.CardBody(
                [
                    dbc.Button(
                        "Enhance Data",
                        id="enhance-btn",
                        color="warning",
                        className="mb-3",
                    ),
                    html.Div(id="enhancement-status"),
                    html.Div(id="enhanced-preview"),
                ]
            ),
        ],
        style=CARD_STYLE,
    )


def create_export_section():
    """Create enhanced export section"""
    return dbc.Card(
        [
            dbc.CardHeader(
                html.H4("Step 6: Export Enhanced Multi-Building Data", className="mb-0")
            ),
            dbc.CardBody(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Button(
                                        "Download CSV",
                                        id="download-csv-btn",
                                        color="info",
                                        className="mb-2",
                                    ),
                                    dcc.Download(id="download-csv"),
                                ],
                                width=4,
                            ),
                            dbc.Col(
                                [
                                    dbc.Button(
                                        "Download JSON",
                                        id="download-json-btn",
                                        color="info",
                                        className="mb-2",
                                    ),
                                    dcc.Download(id="download-json"),
                                ],
                                width=4,
                            ),
                            dbc.Col(
                                [
                                    dbc.Button(
                                        "Building Summary",
                                        id="download-summary-btn",
                                        color="secondary",
                                        className="mb-2",
                                    ),
                                    dcc.Download(id="download-summary"),
                                ],
                                width=4,
                            ),
                        ]
                    ),
                    html.Div(id="export-status"),
                ]
            ),
        ],
        style=CARD_STYLE,
    )


# Create the Dash app
def create_standalone_app():
    """Create the standalone MVP app with enhanced error handling"""
    try:
        # Initialize service container if available
        container = None
        if CONTAINER_AVAILABLE:
            try:
                container = ServiceContainer()
                logger.info("✅ Using existing service container")
            except Exception as e:
                logger.warning(f"⚠️ Service container initialization failed: {e}")

        # Create app
        app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
        app.title = "MVP Data Enhancement Tool - Multi-Building Analysis"

        # Store container reference
        if container:
            app._service_container = container

        return app

    except Exception as e:
        logger.error(f"❌ Failed to create app: {e}")
        raise


# Initialize the app
app = create_standalone_app()

# Main layout with enhanced sections
app.layout = html.Div(
    [
        create_enhanced_header(),
        create_upload_section(),
        create_preview_section(),
        create_column_mapping_section(),
        create_device_mapping_section(),
        create_enhancement_section(),
        create_export_section(),
        # Hidden divs for storing data
        html.Div(id="session-store", style={"display": "none"}),
    ],
    style=CUSTOM_STYLE,
)
