#!/usr/bin/env python3
"""Deep analytics utilities for dashboard pages."""

# =============================================================================
# SECTION 1: CORRECTED IMPORTS (Replace at top of pages/deep_analytics.py)
# =============================================================================

import logging
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
from datetime import datetime

# Dash core imports
from dash import html, dcc, callback, Input, Output, State, ALL, MATCH, ctx
from dash import callback_context
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go

# Add this import
from services import AnalyticsService
from utils.unicode_utils import sanitize_unicode_input, safe_format_number
from utils.preview_utils import serialize_dataframe_preview
from security.unicode_security_handler import UnicodeSecurityHandler

# Internal service imports with CORRECTED paths
ANALYTICS_SERVICE_AVAILABLE = AnalyticsService is not None

from services.data_processing.analytics_engine import (
    AI_SUGGESTIONS_AVAILABLE,
    get_ai_suggestions_for_file,
    get_analytics_service_safe,
    get_data_source_options_safe,
    get_latest_uploaded_source_value,
    get_analysis_type_options,
    clean_analysis_data_unicode,
    process_suggests_analysis,
    process_quality_analysis,
    analyze_data_with_service,
    process_suggests_analysis_safe,
    process_quality_analysis_safe,
    analyze_data_with_service_safe,
)


# AI_SUGGESTIONS_AVAILABLE constant and helper functions are provided by
# ``services.data_processing.analytics_engine``

# Logger setup
logger = logging.getLogger(__name__)


# Helper for display titles
def _get_display_title(analysis_type: str) -> str:
    """Get proper display title for analysis type"""
    title_map = {
        "security": "Security Results",
        "trends": "Trends Results",
        "behavior": "Behavior Results",
        "anomaly": "Anomaly Results",
    }
    return title_map.get(analysis_type.lower(), f"{analysis_type.title()} Results")


# =============================================================================
# SECTION 2: SAFE SERVICE UTILITIES
# Add these utility functions to pages/deep_analytics.py
# =============================================================================





# =============================================================================
# SECTION 3: SUGGESTS ANALYSIS PROCESSOR
# Add this new function to handle suggests display
# =============================================================================





# =============================================================================
# SECTION 4: SUGGESTS DISPLAY COMPONENTS
# Add these functions to create suggests UI components
# =============================================================================


def create_suggests_display(
    suggests_data: Dict[str, Any],
) -> html.Div | dbc.Card | dbc.Alert:
    """Create suggests analysis display components (fixed version)"""
    if "error" in suggests_data:
        return dbc.Alert(f"Error: {suggests_data['error']}", color="danger")

    try:
        filename = suggests_data.get("filename", "Unknown")
        suggestions = suggests_data.get("suggestions", [])
        avg_confidence = suggests_data.get("avg_confidence", 0)
        confident_mappings = suggests_data.get("confident_mappings", 0)
        total_columns = suggests_data.get("total_columns", 0)
        total_rows = suggests_data.get("total_rows", 0)

        # Summary card
        summary_card = dbc.Card(
            [
                dbc.CardHeader(
                    [html.H5(f"🤖 AI Column Mapping Analysis - {filename}")]
                ),
                dbc.CardBody(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.H6("Dataset Info"),
                                        html.P(f"File: {filename}"),
                                        html.P(f"Rows: {total_rows:,}"),
                                        html.P(f"Columns: {total_columns}"),
                                    ],
                                    width=4,
                                ),
                                dbc.Col(
                                    [
                                        html.H6("Overall Confidence"),
                                        dbc.Progress(
                                            value=avg_confidence * 100,
                                            label=f"{avg_confidence:.1%}",
                                            color=(
                                                "success"
                                                if avg_confidence >= 0.7
                                                else (
                                                    "warning"
                                                    if avg_confidence >= 0.4
                                                    else "danger"
                                                )
                                            ),
                                        ),
                                    ],
                                    width=4,
                                ),
                                dbc.Col(
                                    [
                                        html.H6("Confident Mappings"),
                                        html.H3(
                                            f"{confident_mappings}/{total_columns}",
                                            className=(
                                                "text-success"
                                                if confident_mappings
                                                >= total_columns * 0.7
                                                else "text-warning"
                                            ),
                                        ),
                                    ],
                                    width=4,
                                ),
                            ]
                        )
                    ]
                ),
            ],
            className="mb-3",
        )

        # Suggestions table
        if suggestions:
            table_rows = []
            for suggestion in suggestions:
                confidence = suggestion["confidence"]

                table_rows.append(
                    html.Tr(
                        [
                            html.Td(suggestion["column"]),
                            html.Td(suggestion["suggested_field"]),
                            html.Td(
                                [
                                    dbc.Progress(
                                        value=confidence * 100,
                                        label=f"{confidence:.1%}",
                                        color=(
                                            "success"
                                            if confidence >= 0.7
                                            else (
                                                "warning"
                                                if confidence >= 0.4
                                                else "danger"
                                            )
                                        ),
                                    )
                                ]
                            ),
                            html.Td(suggestion["status"]),
                            html.Td(
                                html.Small(
                                    str(suggestion["sample_data"][:2]),
                                    className="text-muted",
                                )
                            ),
                        ]
                    )
                )

            suggestions_table = dbc.Card(
                [
                    dbc.CardHeader([html.H6("📋 Column Mapping Suggestions")]),
                    dbc.CardBody(
                        [
                            dbc.Table(
                                [
                                    html.Thead(
                                        [
                                            html.Tr(
                                                [
                                                    html.Th("Column Name"),
                                                    html.Th("Suggested Field"),
                                                    html.Th("Confidence"),
                                                    html.Th("Status"),
                                                    html.Th("Sample Data"),
                                                ]
                                            )
                                        ]
                                    ),
                                    html.Tbody(table_rows),
                                ],
                                responsive=True,
                                striped=True,
                            )
                        ]
                    ),
                ],
                className="mb-3",
            )
        else:
            suggestions_table = dbc.Alert("No suggestions available", color="warning")

        return html.Div([summary_card, suggestions_table])

    except Exception as e:
        logger.exception("Error creating suggests display: %s", e)
        return dbc.Alert(f"Error creating display: {str(e)}", color="danger")


# =============================================================================
# DEEP ANALYTICS BUTTON REPLACEMENT HELPERS
# =============================================================================


def get_analysis_buttons_section():
    """Replace the analytics-type dropdown column with this"""
    return dbc.Col(
        [
            html.Label(
                "Analysis Type",
                htmlFor="security-btn",
                className="fw-bold mb-3",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Button(
                                "🔒 Security Analysis",
                                id="security-btn",
                                color="danger",
                                outline=True,
                                size="sm",
                                className="w-100 mb-2",
                            )
                        ],
                        width=6,
                    ),
                    dbc.Col(
                        [
                            dbc.Button(
                                "📈 Trends Analysis",
                                id="trends-btn",
                                color="info",
                                outline=True,
                                size="sm",
                                className="w-100 mb-2",
                            )
                        ],
                        width=6,
                    ),
                    dbc.Col(
                        [
                            dbc.Button(
                                "👤 Behavior Analysis",
                                id="behavior-btn",
                                color="warning",
                                outline=True,
                                size="sm",
                                className="w-100 mb-2",
                            )
                        ],
                        width=6,
                    ),
                    dbc.Col(
                        [
                            dbc.Button(
                                "🚨 Anomaly Detection",
                                id="anomaly-btn",
                                color="dark",
                                outline=True,
                                size="sm",
                                className="w-100 mb-2",
                            )
                        ],
                        width=6,
                    ),
                    dbc.Col(
                        [
                            dbc.Button(
                                "🤖 AI Suggestions",
                                id="suggests-btn",
                                color="success",
                                outline=True,
                                size="sm",
                                className="w-100 mb-2",
                            )
                        ],
                        width=6,
                    ),
                    dbc.Col(
                        [
                            dbc.Button(
                                "💰 Data Quality",
                                id="quality-btn",
                                color="secondary",
                                outline=True,
                                size="sm",
                                className="w-100 mb-2",
                            )
                        ],
                        width=6,
                    ),
                    dbc.Col(
                        [
                            dbc.Button(
                                "Unique Patterns",
                                id="unique-patterns-btn",
                                color="primary",
                                outline=True,
                                size="sm",
                                className="w-100 mb-2",
                            )
                        ],
                        width=6,
                    ),
                ]
            ),
        ],
        width=6,
    )


def get_updated_button_group():
    """Replace the generate analytics button group with this"""
    return dbc.ButtonGroup(
        [
            dbc.Button(
                "🔄 Refresh Data Sources",
                id="refresh-sources-btn",
                color="outline-secondary",
                size="lg",
            )
        ]
    )


def get_initial_message():
    """Initial message when no button clicked"""
    return dbc.Alert(
        [
            html.H6("👈 Get Started"),
            html.P("1. Select a data source from dropdown"),
            html.P("2. Click any analysis button to run immediately"),
            html.P("Each button runs its analysis type automatically"),
        ],
        color="info",
    )


# =============================================================================
# SECTION 5: LAYOUT FUNCTION REPLACEMENT
# COMPLETELY REPLACE the layout() function in pages/deep_analytics.py
# =============================================================================


# =============================================================================
# SECTION 7: HELPER DISPLAY FUNCTIONS
# Add these helper functions for non-suggests analysis types
# =============================================================================





def create_data_quality_display_corrected(
    data_source: str,
) -> html.Div | dbc.Card | dbc.Alert:
    """Data quality analysis with proper imports"""
    try:
        # Handle BOTH upload formats
        if data_source.startswith("upload:") or data_source == "service:uploaded":

            if data_source.startswith("upload:"):
                filename = data_source.replace("upload:", "")
            else:
                filename = None

            from pages.file_upload import get_uploaded_data

            uploaded_files = get_uploaded_data()

            if not uploaded_files:
                return dbc.Alert("No uploaded files found", color="warning")

            # If no specific filename, use the first available file
            if filename is None or filename not in uploaded_files:
                filename = list(uploaded_files.keys())[0]

            if filename in uploaded_files:
                df = uploaded_files[filename]

                total_rows = len(df)
                total_cols = len(df.columns)
                missing_values = df.isnull().sum().sum()
                duplicate_rows = df.duplicated().sum()

                quality_score = max(
                    0,
                    100
                    - (missing_values / (total_rows * total_cols) * 100)
                    - (duplicate_rows / total_rows * 10),
                )

                return dbc.Card(
                    [
                        dbc.CardHeader(
                            [html.H5(f"📊 Data Quality Analysis - {filename}")]
                        ),
                        dbc.CardBody(
                            [
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            [
                                                html.H6("Dataset Overview"),
                                                html.P(f"File: {filename}"),
                                                html.P(f"Rows: {total_rows:,}"),
                                                html.P(f"Columns: {total_cols}"),
                                                html.P(
                                                    f"Missing values: {missing_values:,}"
                                                ),
                                                html.P(
                                                    f"Duplicate rows: {duplicate_rows:,}"
                                                ),
                                            ],
                                            width=6,
                                        ),
                                        dbc.Col(
                                            [
                                                html.H6("Quality Score"),
                                                dbc.Progress(
                                                    value=quality_score,
                                                    label=f"{quality_score:.1f}%",
                                                    color=(
                                                        "success"
                                                        if quality_score >= 80
                                                        else (
                                                            "warning"
                                                            if quality_score >= 60
                                                            else "danger"
                                                        )
                                                    ),
                                                ),
                                            ],
                                            width=6,
                                        ),
                                    ]
                                )
                            ]
                        ),
                    ]
                )

        return dbc.Alert(
            "Data quality analysis only available for uploaded files", color="info"
        )
    except Exception as e:
        logger.exception("Quality analysis display error: %s", e)
        return dbc.Alert(f"Quality analysis error: {str(e)}", color="danger")





# Helper extraction functions for results processing
def _extract_counts(results: Dict[str, Any]) -> Dict[str, int | float]:
    """Extract proper counts from results handling sets and other iterables"""
    total_events = results.get("total_events", 0)

    def _normalize_count(value: Any) -> int:
        if value is None:
            return 0
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return int(value)
        if hasattr(value, "__len__") and not isinstance(value, (str, bytes)):
            try:
                return len(value)
            except Exception:
                pass
        if hasattr(value, "__iter__") and not isinstance(value, (str, bytes)):
            try:
                return len(list(value))
            except Exception:
                pass
        try:
            return int(value)
        except Exception:
            return 0

    unique_users = _normalize_count(results.get("unique_users", 0))
    unique_doors = _normalize_count(results.get("unique_doors", 0))

    success_rate = results.get("success_rate", 0)
    if not success_rate:
        success_rate = results.get("overall_success_rate", 0)
    if not success_rate:
        pct = (
            results.get("success_percentage")
            or results.get("success_rate_percentage")
            or results.get("success_percent")
        )
        if pct:
            success_rate = pct / 100 if pct > 1 else pct
    if not success_rate:
        successful = results.get("successful_events", 0)
        failed = results.get("failed_events", 0)
        if (successful + failed) > 0:
            success_rate = successful / (successful + failed)

    return {
        "total_events": total_events,
        "unique_users": unique_users,
        "unique_doors": unique_doors,
        "success_rate": success_rate,
    }


def _extract_security_metrics(results: Dict[str, Any]) -> Dict[str, Any]:
    """Extract security-specific metrics from results"""
    security_score_raw = results.get("security_score", {})

    if hasattr(security_score_raw, "score"):
        score_val = float(security_score_raw.score)
        risk_level = security_score_raw.threat_level.title()
    elif isinstance(security_score_raw, dict):
        score_val = float(security_score_raw.get("score", 0.0))
        risk_level = security_score_raw.get("threat_level", "unknown").title()
    else:
        score_val = float(security_score_raw) if security_score_raw else 0.0
        risk_level = "Unknown"

    failed_attempts = results.get("failed_attempts", 0)
    if failed_attempts == 0:
        failed_attempts = results.get("failed_events", 0)

    success_rate = results.get("success_rate", 0)
    if not success_rate:
        success_rate = results.get("overall_success_rate", 0)
    if not success_rate:
        pct = (
            results.get("success_percentage")
            or results.get("success_rate_percentage")
            or results.get("success_percent")
        )
        if pct:
            success_rate = pct / 100 if pct > 1 else pct
    if not success_rate:
        successful = results.get("successful_events", 0)
        failed = results.get("failed_events", 0)
        if (successful + failed) > 0:
            success_rate = successful / (successful + failed)

    return {
        "score": score_val,
        "risk_level": risk_level,
        "failed_attempts": failed_attempts,
        "success_rate": success_rate,
    }


def _extract_enhanced_security_details(results: Dict[str, Any]) -> Dict[str, Any]:
    """Return extended security analysis details."""
    threats = results.get("threats", [])
    if not isinstance(threats, list):
        threats = []

    threat_count = results.get("threat_count")
    if threat_count is None:
        threat_count = len(threats)

    critical_threats = results.get("critical_threats")
    if critical_threats is None:
        critical_threats = len(
            [t for t in threats if str(t.get("severity", "")).lower() == "critical"]
        )

    ci_raw = results.get("confidence_interval", (0.0, 0.0))
    if isinstance(ci_raw, (list, tuple)) and len(ci_raw) == 2:
        try:
            confidence_interval = (float(ci_raw[0]), float(ci_raw[1]))
        except (TypeError, ValueError):
            confidence_interval = (0.0, 0.0)
    else:
        confidence_interval = (0.0, 0.0)

    recommendations = results.get("recommendations", [])
    if not isinstance(recommendations, list):
        recommendations = [str(recommendations)] if recommendations else []

    top_threats: List[str] = []
    if threats:
        sorted_threats = sorted(
            threats, key=lambda x: float(x.get("confidence", 0)), reverse=True
        )[:3]
        for t in sorted_threats:
            desc = t.get("description") or t.get("type", "Unknown")
            severity = str(t.get("severity", "unknown")).title()
            top_threats.append(f"{severity}: {desc}")

    return {
        "threat_count": threat_count,
        "critical_threats": critical_threats,
        "confidence_interval": confidence_interval,
        "recommendations": recommendations,
        "top_threats": top_threats,
    }


def create_analysis_results_display(
    results: Dict[str, Any], analysis_type: str
) -> html.Div | dbc.Card | dbc.Alert:
    """Create display for different analysis types"""
    try:
        counts = _extract_counts(results)
        total_events = counts["total_events"]
        unique_users = counts["unique_users"]
        unique_doors = counts["unique_doors"]
        success_rate = counts["success_rate"]
        analysis_focus = results.get("analysis_focus", "")

        # Create type-specific content
        if analysis_type == "security":
            sec_metrics = _extract_security_metrics(results)
            sec_details = _extract_enhanced_security_details(results)
            specific_content = [
                html.P(f"Security Score: {sec_metrics['score']:.1f}/100"),
                html.P(f"Failed Attempts: {sec_metrics['failed_attempts']:,}"),
                html.P(f"Risk Level: {sec_metrics['risk_level']}"),
                html.P(
                    f"Threats: {sec_details['threat_count']} (Critical: {sec_details['critical_threats']})"
                ),
                html.P(
                    "Confidence Interval: "
                    f"{sec_details['confidence_interval'][0]:.1f}-{sec_details['confidence_interval'][1]:.1f}"
                ),
            ]

            if sec_details["recommendations"]:
                specific_content.append(html.H6("Recommendations"))
                specific_content.append(
                    html.Ul([html.Li(r) for r in sec_details["recommendations"]])
                )
            if sec_details["top_threats"]:
                specific_content.append(html.H6("Top Threats"))
                specific_content.append(
                    html.Ul([html.Li(t) for t in sec_details["top_threats"]])
                )

            color = (
                "danger"
                if sec_metrics["risk_level"] == "High"
                else "warning" if sec_metrics["risk_level"] == "Medium" else "success"
            )

        elif analysis_type == "trends":
            specific_content = [
                html.P(f"Daily Average: {results.get('daily_average', 0):.0f} events"),
                html.P(f"Peak Usage: {results.get('peak_usage', 'Unknown')}"),
                html.P(f"Trend: {results.get('trend_direction', 'Unknown')}"),
            ]
            color = "info"

        elif analysis_type == "behavior":
            specific_content = [
                html.P(
                    f"Avg Accesses/User: {results.get('avg_accesses_per_user', 0):.1f}"
                ),
                html.P(f"Heavy Users: {results.get('heavy_users', 0)}"),
                html.P(f"Behavior Score: {results.get('behavior_score', 'Unknown')}"),
            ]
            color = "success"

        elif analysis_type == "anomaly":
            specific_content = [
                html.P(f"Anomalies Detected: {results.get('anomalies_detected', 0):,}"),
                html.P(f"Threat Level: {results.get('threat_level', 'Unknown')}"),
                html.P(f"Status: {results.get('suspicious_activities', 'Unknown')}"),
            ]
            color = "danger" if results.get("threat_level") == "Critical" else "warning"

        else:
            specific_content = [html.P("Standard analysis completed")]
            color = "info"

        title_safe = sanitize_unicode_input(_get_display_title(analysis_type))
        events_safe = safe_format_number(total_events)
        users_safe = safe_format_number(unique_users)
        doors_safe = safe_format_number(unique_doors)

        return dbc.Card(
            [
                dbc.CardHeader([html.H5(f"📊 {title_safe}")]),
                dbc.CardBody(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.H6("📈 Summary"),
                                        html.P(f"Total Events: {events_safe}"),
                                        html.P(f"Unique Users: {users_safe}"),
                                        html.P(f"Unique Doors: {doors_safe}"),
                                        dbc.Progress(
                                            value=success_rate * 100,
                                            label=f"Success Rate: {success_rate:.1%}",
                                            color=(
                                                "success"
                                                if success_rate > 0.8
                                                else "warning"
                                            ),
                                        ),
                                    ],
                                    width=6,
                                ),
                                dbc.Col(
                                    [
                                        html.H6(f"🎯 {analysis_type.title()} Specific"),
                                        html.Div(specific_content),
                                    ],
                                    width=6,
                                ),
                            ]
                        ),
                        html.Hr(),
                        dbc.Alert(
                            [html.H6("Analysis Focus"), html.P(analysis_focus)],
                            color=color,
                        ),
                    ]
                ),
            ]
        )
    except Exception as e:
        logger.exception("Error displaying results: %s", e)
        return dbc.Alert(f"Error displaying results: {str(e)}", color="danger")


def create_limited_analysis_display(
    data_source: str, analysis_type: str
) -> html.Div | dbc.Card:
    """Create limited analysis display when service unavailable"""
    return dbc.Card(
        [
            dbc.CardHeader([html.H5(f"⚠️ Limited {analysis_type.title()} Analysis")]),
            dbc.CardBody(
                [
                    dbc.Alert(
                        [
                            html.H6("Service Limitations"),
                            html.P("Full analytics service is not available."),
                            html.P("Basic analysis results would be shown here."),
                        ],
                        color="warning",
                    ),
                    html.P(f"Data source: {data_source}"),
                    html.P(f"Analysis type: {analysis_type}"),
                ]
            ),
        ]
    )


def create_data_quality_display(data_source: str) -> html.Div | dbc.Card | dbc.Alert:
    """Create data quality analysis display"""
    try:
        if data_source.startswith("upload:"):
            filename = data_source.replace("upload:", "")
            from utils.upload_store import uploaded_data_store

            if filename in uploaded_data_store.get_filenames():
                df = uploaded_data_store.load_dataframe(filename)

                # Basic quality metrics
                total_rows = len(df)
                total_cols = len(df.columns)
                missing_values = df.isnull().sum().sum()
                duplicate_rows = df.duplicated().sum()

                return dbc.Card(
                    [
                        dbc.CardHeader([html.H5("📊 Data Quality Analysis")]),
                        dbc.CardBody(
                            [
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            [
                                                html.H6("Dataset Overview"),
                                                html.P(f"Rows: {total_rows:,}"),
                                                html.P(f"Columns: {total_cols}"),
                                                html.P(
                                                    f"Missing values: {missing_values:,}"
                                                ),
                                                html.P(
                                                    f"Duplicate rows: {duplicate_rows:,}"
                                                ),
                                            ],
                                            width=6,
                                        ),
                                        dbc.Col(
                                            [
                                                html.H6("Quality Score"),
                                                dbc.Progress(
                                                    value=max(
                                                        0,
                                                        100
                                                        - (
                                                            missing_values
                                                            / total_rows
                                                            * 100
                                                        )
                                                        - (
                                                            duplicate_rows
                                                            / total_rows
                                                            * 10
                                                        ),
                                                    ),
                                                    label="Quality",
                                                    color="success",
                                                ),
                                            ],
                                            width=6,
                                        ),
                                    ]
                                )
                            ]
                        ),
                    ]
                )
        return dbc.Alert(
            "Data quality analysis only available for uploaded files", color="info"
        )
    except Exception as e:
        logger.exception("Quality analysis error: %s", e)
        return dbc.Alert(f"Quality analysis error: {str(e)}", color="danger")


def get_initial_message_safe():
    """Initial message with safe ASCII text"""
    return dbc.Alert(
        [
            html.H6("Get Started"),
            html.P("1. Select a data source from dropdown"),
            html.P("2. Click any analysis button to run immediately"),
            html.P("Each button runs its analysis type automatically"),
        ],
        color="info",
    )





def create_analysis_results_display_safe(results, analysis_type):
    """Create safe results display without Unicode issues"""
    try:
        if isinstance(results, dict) and "error" in results:
            return dbc.Alert(str(results["error"]), color="danger")
        content = [html.H5(f"{analysis_type.title()} Results"), html.Hr()]
        if analysis_type == "suggests" and "suggestions" in results:
            content.extend(
                [
                    html.P(f"File: {results.get('filename', 'Unknown')}"),
                    html.P(f"Columns analyzed: {results.get('total_columns', 0)}"),
                    html.P(f"Rows processed: {results.get('total_rows', 0)}"),
                    html.H6("AI Column Suggestions:"),
                    html.Div(
                        [
                            html.P(
                                f"{col}: {info.get('field', 'unknown')} (confidence: {info.get('confidence', 0):.1f})"
                            )
                            for col, info in results.get("suggestions", {}).items()
                        ]
                    ),
                ]
            )
        elif analysis_type == "quality":
            content.extend(
                [
                    html.P(f"Total rows: {results.get('total_rows', 0):,}"),
                    html.P(f"Total columns: {results.get('total_columns', 0)}"),
                    html.P(f"Missing values: {results.get('missing_values', 0):,}"),
                    html.P(f"Duplicate rows: {results.get('duplicate_rows', 0):,}"),
                    html.P(f"Quality score: {results.get('quality_score', 0):.1f}%"),
                ]
            )
        else:
            content.extend(
                [
                    html.P(f"Total events: {results.get('total_events', 0):,}"),
                    html.P(f"Unique users: {results.get('unique_users', 0):,}"),
                    html.P(f"Success rate: {results.get('success_rate', 0):.1%}"),
                ]
            )
        return dbc.Card([dbc.CardBody(content)])
    except Exception as e:
        logger.exception("Display error: %s", e)
        return dbc.Alert(f"Display error: {str(e)}", color="danger")
