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
from services import AnalyticsService, get_analytics_service
from utils.unicode_utils import sanitize_unicode_input, safe_format_number
from utils.preview_utils import serialize_dataframe_preview
from security.unicode_security_handler import UnicodeSecurityHandler

# Internal service imports with CORRECTED paths
ANALYTICS_SERVICE_AVAILABLE = AnalyticsService is not None

from services.ai_suggestions import generate_column_suggestions
from services.analytics_processing import (
    process_suggests_analysis as service_process_suggests_analysis,
    create_suggests_display as service_create_suggests_display,
    process_quality_analysis as service_process_quality_analysis,
    create_data_quality_display as service_create_data_quality_display,
    analyze_data_with_service as service_analyze_data_with_service,
    create_analysis_results_display as service_create_analysis_results_display,
)



def get_ai_suggestions_for_file(
    df: pd.DataFrame, filename: str
) -> Dict[str, Dict[str, Any]]:
    """Return AI column suggestions for ``df`` columns."""
    try:
        return get_ai_column_suggestions(list(df.columns))
    except Exception:
        suggestions: Dict[str, Dict[str, Any]] = {}
        for col in df.columns:
            col_lower = col.lower().strip()
            if any(word in col_lower for word in ["time", "date", "stamp"]):
                suggestions[col] = {"field": "timestamp", "confidence": 0.8}
            elif any(word in col_lower for word in ["person", "user", "employee"]):
                suggestions[col] = {"field": "person_id", "confidence": 0.7}
            elif any(word in col_lower for word in ["door", "location", "device"]):
                suggestions[col] = {"field": "door_id", "confidence": 0.7}
            elif any(word in col_lower for word in ["access", "result", "status"]):
                suggestions[col] = {"field": "access_result", "confidence": 0.6}
            elif any(word in col_lower for word in ["token", "badge", "card"]):
                suggestions[col] = {"field": "token_id", "confidence": 0.6}
            else:
                suggestions[col] = {"field": "", "confidence": 0.0}
        return suggestions


AI_SUGGESTIONS_AVAILABLE = True

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


def get_analytics_service_safe():
    """Safely return the shared analytics service instance."""
    if get_analytics_service is None:
        return None
    try:
        return get_analytics_service()
    except Exception as e:
        logger.exception("Failed to initialize AnalyticsService: %s", e)
        return None


def get_data_source_options_safe():
    """Get data source options without Unicode issues"""
    options = []
    try:
        from pages.file_upload import get_uploaded_data

        uploaded_files = get_uploaded_data()
        if uploaded_files:
            for filename in uploaded_files.keys():
                options.append(
                    {"label": f"File: {filename}", "value": f"upload:{filename}"}
                )
    except ImportError:
        pass
    try:
        service = get_analytics_service_safe()
        if service:
            service_sources = service.get_data_source_options()
            for source_dict in service_sources:
                if isinstance(source_dict, dict):
                    label = source_dict.get("label", "Unknown")
                    value = source_dict.get("value", "unknown")
                else:
                    # Backwards compatibility if service returns strings
                    label = str(source_dict)
                    value = str(source_dict)
                options.append(
                    {"label": f"Service: {label}", "value": f"service:{value}"}
                )
    except Exception as e:
        logger.exception("Error getting service data sources: %s", e)
    if not options:
        options.append(
            {"label": "No data sources available - Upload files first", "value": "none"}
        )
    return options


def get_latest_uploaded_source_value() -> Optional[str]:
    """Return dropdown value for the most recently uploaded file"""
    try:
        from pages.file_upload import get_uploaded_filenames

        filenames = get_uploaded_filenames()
        if filenames:
            # Use the last filename in the list which represents the
            # most recently uploaded file because the underlying store
            # preserves insertion order.
            return f"upload:{filenames[-1]}"
    except ImportError as e:
        logger.error("File upload utilities missing: %s", e)
    except Exception as e:
        logger.exception("Failed to get latest uploaded source value: %s", e)
    return None


def get_analysis_type_options() -> List[Dict[str, str]]:
    """Get available analysis types including suggests analysis"""
    return [
        {"label": "🔒 Security Patterns", "value": "security"},
        {"label": "📈 Access Trends", "value": "trends"},
        {"label": "👤 User Behavior", "value": "behavior"},
        {"label": "🚨 Anomaly Detection", "value": "anomaly"},
        {"label": "🤖 AI Column Suggestions", "value": "suggests"},
        {"label": "📊 Data Quality", "value": "quality"},
    ]


def clean_analysis_data_unicode(df: pd.DataFrame) -> pd.DataFrame:
    """Return DataFrame sanitized for Unicode issues."""
    try:
        return UnicodeSecurityHandler.sanitize_dataframe(df)
    except Exception as e:
        logger.exception("Unicode sanitization failed: %s", e)
        return df


# =============================================================================
# SECTION 3: SUGGESTS ANALYSIS PROCESSOR
# Add this new function to handle suggests display
# =============================================================================


def process_suggests_analysis(data_source: str) -> Dict[str, Any]:
    """Process AI suggestions analysis via service layer."""
    return service_process_suggests_analysis(data_source)


# =============================================================================
# SECTION 4: SUGGESTS DISPLAY COMPONENTS
# Add these functions to create suggests UI components
# =============================================================================


def create_suggests_display(
    suggests_data: Dict[str, Any],
) -> html.Div | dbc.Card | dbc.Alert:
    """Create suggests analysis display using the service layer."""
    return service_create_suggests_display(suggests_data)


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


def analyze_data_with_service(data_source: str, analysis_type: str) -> Dict[str, Any]:
    """Generate analysis using the analytics service with chunked processing."""
    return service_analyze_data_with_service(data_source, analysis_type)


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


def process_quality_analysis(data_source: str) -> Dict[str, Any]:
    """Basic processing for data quality analysis via service layer."""
    return service_process_quality_analysis(data_source)


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
    """Create display for different analysis types via service layer."""
    return service_create_analysis_results_display(results, analysis_type)


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
    """Create data quality analysis display via service layer."""
    return service_create_data_quality_display(data_source)


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


def process_suggests_analysis_safe(data_source):
    """Safe AI suggestions analysis"""
    try:
        if data_source.startswith("upload:") or data_source == "service:uploaded":
            from pages.file_upload import get_uploaded_data

            uploaded_files = get_uploaded_data()
            if not uploaded_files:
                return {"error": "No uploaded files found"}
            filename = (
                data_source.replace("upload:", "")
                if data_source.startswith("upload:")
                else list(uploaded_files.keys())[0]
            )
            df = uploaded_files.get(filename)
            if df is None:
                return {"error": f"File {filename} not found"}
            suggestions = {}
            for col in df.columns:
                col_lower = str(col).lower().strip()
                if any(word in col_lower for word in ["time", "date", "stamp"]):
                    suggestions[col] = {"field": "timestamp", "confidence": 0.8}
                elif any(word in col_lower for word in ["person", "user", "employee"]):
                    suggestions[col] = {"field": "person_id", "confidence": 0.7}
                elif any(word in col_lower for word in ["door", "location", "device"]):
                    suggestions[col] = {"field": "door_id", "confidence": 0.7}
                else:
                    suggestions[col] = {"field": "other", "confidence": 0.5}
            return {
                "analysis_type": "AI Column Suggestions",
                "filename": filename,
                "suggestions": suggestions,
                "total_columns": len(df.columns),
                "total_rows": len(df),
            }
        return {"error": "AI suggestions only available for uploaded files"}
    except Exception as e:
        logger.exception("AI analysis error: %s", e)
        return {"error": f"AI analysis error: {str(e)}"}


def process_quality_analysis_safe(data_source):
    """Safe data quality analysis"""
    try:
        if data_source.startswith("upload:") or data_source == "service:uploaded":
            from pages.file_upload import get_uploaded_data

            uploaded_files = get_uploaded_data()
            if not uploaded_files:
                return {"error": "No uploaded files found"}
            filename = (
                data_source.replace("upload:", "")
                if data_source.startswith("upload:")
                else list(uploaded_files.keys())[0]
            )
            df = uploaded_files.get(filename)
            if df is None:
                return {"error": f"File {filename} not found"}
            total_rows = len(df)
            total_cols = len(df.columns)
            missing_values = df.isnull().sum().sum()
            duplicate_rows = df.duplicated().sum()
            quality_score = max(
                0, 100 - (missing_values + duplicate_rows) / total_rows * 100
            )
            return {
                "analysis_type": "Data Quality",
                "filename": filename,
                "total_rows": total_rows,
                "total_columns": total_cols,
                "missing_values": int(missing_values),
                "duplicate_rows": int(duplicate_rows),
                "quality_score": round(quality_score, 1),
            }
        return {"error": "Data quality analysis only available for uploaded files"}
    except Exception as e:
        logger.exception("Quality analysis error: %s", e)
        return {"error": f"Quality analysis error: {str(e)}"}


def analyze_data_with_service_safe(data_source, analysis_type):
    """Safe service-based analysis"""
    try:
        service = get_analytics_service_safe()
        if not service:
            return {"error": "Analytics service not available"}
        source_name = (
            data_source.replace("service:", "")
            if data_source.startswith("service:")
            else "uploaded"
        )
        analytics_results = service.get_analytics_by_source(source_name)
        if analytics_results.get("status") == "error":
            return {"error": analytics_results.get("message", "Unknown error")}
        return {
            "analysis_type": analysis_type.title(),
            "data_source": data_source,
            "total_events": analytics_results.get("total_events", 0),
            "unique_users": analytics_results.get("unique_users", 0),
            "success_rate": analytics_results.get("success_rate", 0),
            "status": "completed",
        }
    except Exception as e:
        logger.exception("Service analysis failed: %s", e)
        return {"error": f"Service analysis failed: {str(e)}"}


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
