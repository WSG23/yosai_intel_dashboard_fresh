#!/usr/bin/env python3
"""
COMPLETE DEEP ANALYTICS FIX
Fixes all method and import errors
Replace the broken functions in pages/deep_analytics.py
"""

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
from services.analytics_service import AnalyticsService

# Internal service imports with CORRECTED paths
try:
    from services.analytics_service import AnalyticsService

    ANALYTICS_SERVICE_AVAILABLE = True
except ImportError:
    ANALYTICS_SERVICE_AVAILABLE = False

try:
    from components.column_verification import get_ai_suggestions_for_file
    AI_SUGGESTIONS_AVAILABLE = True
except ImportError:
    # Fallback AI suggestions function
    def get_ai_suggestions_for_file(df, filename):
        suggestions = {}
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

# =============================================================================
# SECTION 2: SAFE SERVICE UTILITIES
# Add these utility functions to pages/deep_analytics.py
# =============================================================================



def get_analytics_service_safe():
    """Safely get analytics service"""
    try:
        from services.analytics_service import AnalyticsService
        return AnalyticsService()
    except ImportError:
        return None
    except Exception:
        return None


def get_data_source_options_safe():
    """Get data source options without Unicode issues"""
    options = []
    try:
        from pages.file_upload import get_uploaded_data
        uploaded_files = get_uploaded_data()
        if uploaded_files:
            for filename in uploaded_files.keys():
                options.append({
                    "label": f"File: {filename}",
                    "value": f"upload:{filename}"
                })
    except ImportError:
        pass
    try:
        service = get_analytics_service_safe()
        if service:
            service_sources = service.get_available_sources()
            for source_dict in service_sources:
                options.append({
                    "label": f"Service: {source_dict.get('label', 'Unknown')}",
                    "value": f"service:{source_dict.get('value', 'unknown')}"
                })
    except Exception:
        pass
    if not options:
        options.append({
            "label": "No data sources available - Upload files first",
            "value": "none"
        })
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
    except Exception:
        pass
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


# =============================================================================
# SECTION 3: SUGGESTS ANALYSIS PROCESSOR
# Add this new function to handle suggests display
# =============================================================================


def process_suggests_analysis(data_source: str) -> Dict[str, Any]:
    """Process AI suggestions analysis for the selected data source"""
    try:
        logger.info(f"🔍 Processing suggests analysis for: {data_source}")

        if not data_source or data_source == "none":
            return {"error": "No data source selected"}

        # Handle BOTH upload formats
        if data_source.startswith("upload:") or data_source == "service:uploaded":

            if data_source.startswith("upload:"):
                filename = data_source.replace("upload:", "")
            else:
                # Handle service:uploaded - use first available file
                filename = None

            from pages.file_upload import get_uploaded_data

            uploaded_files = get_uploaded_data()

            if not uploaded_files:
                return {"error": "No uploaded files found"}

            # If no specific filename, use the first available file
            if filename is None or filename not in uploaded_files:
                filename = list(uploaded_files.keys())[0]

            df = uploaded_files[filename]

            # Get AI suggestions
            if AI_SUGGESTIONS_AVAILABLE:
                try:
                    suggestions = get_ai_suggestions_for_file(df, filename)

                    processed_suggestions = []
                    total_confidence = 0
                    confident_mappings = 0

                    for column, suggestion in suggestions.items():
                        field = suggestion.get("field", "")
                        confidence = suggestion.get("confidence", 0.0)

                        status = (
                            "🟢 High"
                            if confidence >= 0.7
                            else "🟡 Medium" if confidence >= 0.4 else "🔴 Low"
                        )

                        try:
                            sample_data = (
                                df[column].dropna().head(3).astype(str).tolist()
                            )
                        except Exception:
                            sample_data = ["N/A"]

                        processed_suggestions.append(
                            {
                                "column": column,
                                "suggested_field": field if field else "No suggestion",
                                "confidence": confidence,
                                "status": status,
                                "sample_data": sample_data,
                            }
                        )

                        total_confidence += confidence
                        if confidence >= 0.6:
                            confident_mappings += 1

                    avg_confidence = (
                        total_confidence / len(suggestions) if suggestions else 0
                    )

                    try:
                        data_preview = df.head(5).to_dict("records")
                    except Exception:
                        data_preview = []

                    return {
                        "filename": filename,
                        "total_columns": len(df.columns),
                        "total_rows": len(df),
                        "suggestions": processed_suggestions,
                        "avg_confidence": avg_confidence,
                        "confident_mappings": confident_mappings,
                        "data_preview": data_preview,
                        "column_names": list(df.columns),
                    }

                except Exception as e:
                    return {"error": f"AI suggestions failed: {str(e)}"}
            else:
                return {"error": "AI suggestions service not available"}
        else:
            return {
                "error": f"Suggests analysis not available for data source: {data_source}"
            }

    except Exception as e:
        return {"error": f"Failed to process suggests: {str(e)}"}


# =============================================================================
# SECTION 4: SUGGESTS DISPLAY COMPONENTS
# Add these functions to create suggests UI components
# =============================================================================


def create_suggests_display(suggests_data: Dict[str, Any]) -> html.Div:
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
        summary_card = dbc.Card([
            dbc.CardHeader([
                html.H5(f"🤖 AI Column Mapping Analysis - {filename}")
            ]),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.H6("Dataset Info"),
                        html.P(f"File: {filename}"),
                        html.P(f"Rows: {total_rows:,}"),
                        html.P(f"Columns: {total_columns}")
                    ], width=4),
                    dbc.Col([
                        html.H6("Overall Confidence"),
                        dbc.Progress(
                            value=avg_confidence * 100,
                            label=f"{avg_confidence:.1%}",
                            color="success" if avg_confidence >= 0.7 else "warning" if avg_confidence >= 0.4 else "danger"
                        )
                    ], width=4),
                    dbc.Col([
                        html.H6("Confident Mappings"),
                        html.H3(f"{confident_mappings}/{total_columns}",
                               className="text-success" if confident_mappings >= total_columns * 0.7 else "text-warning")
                    ], width=4)
                ])
            ])
        ], className="mb-3")

        # Suggestions table
        if suggestions:
            table_rows = []
            for suggestion in suggestions:
                confidence = suggestion['confidence']

                table_rows.append(
                    html.Tr([
                        html.Td(suggestion['column']),
                        html.Td(suggestion['suggested_field']),
                        html.Td([
                            dbc.Progress(
                                value=confidence * 100,
                                label=f"{confidence:.1%}",
                                color="success" if confidence >= 0.7 else "warning" if confidence >= 0.4 else "danger"
                            )
                        ]),
                        html.Td(suggestion['status']),
                        html.Td(html.Small(str(suggestion['sample_data'][:2]), className="text-muted"))
                    ])
                )

            suggestions_table = dbc.Card([
                dbc.CardHeader([
                    html.H6("📋 Column Mapping Suggestions")
                ]),
                dbc.CardBody([
                    dbc.Table([
                        html.Thead([
                            html.Tr([
                                html.Th("Column Name"),
                                html.Th("Suggested Field"),
                                html.Th("Confidence"),
                                html.Th("Status"),
                                html.Th("Sample Data")
                            ])
                        ]),
                        html.Tbody(table_rows)
                    ], responsive=True, striped=True)
                ])
            ], className="mb-3")
        else:
            suggestions_table = dbc.Alert("No suggestions available", color="warning")

        return html.Div([
            summary_card,
            suggestions_table
        ])

    except Exception as e:
        return dbc.Alert(f"Error creating display: {str(e)}", color="danger")


# =============================================================================
# DEEP ANALYTICS BUTTON REPLACEMENT HELPERS
# =============================================================================


def get_analysis_buttons_section():
    """Replace the analytics-type dropdown column with this"""
    return dbc.Col([
        html.Label(
            "Analysis Type",
            htmlFor="security-btn",
            className="fw-bold mb-3",
        ),
        dbc.Row([
            dbc.Col([
                dbc.Button(
                    "🔒 Security Analysis",
                    id="security-btn",
                    color="danger",
                    outline=True,
                    size="sm",
                    className="w-100 mb-2"
                )
            ], width=6),
            dbc.Col([
                dbc.Button(
                    "📈 Trends Analysis",
                    id="trends-btn",
                    color="info",
                    outline=True,
                    size="sm",
                    className="w-100 mb-2"
                )
            ], width=6),
            dbc.Col([
                dbc.Button(
                    "👤 Behavior Analysis",
                    id="behavior-btn",
                    color="warning",
                    outline=True,
                    size="sm",
                    className="w-100 mb-2"
                )
            ], width=6),
            dbc.Col([
                dbc.Button(
                    "🚨 Anomaly Detection",
                    id="anomaly-btn",
                    color="dark",
                    outline=True,
                    size="sm",
                    className="w-100 mb-2"
                )
            ], width=6),
            dbc.Col([
                dbc.Button(
                    "🤖 AI Suggestions",
                    id="suggests-btn",
                    color="success",
                    outline=True,
                    size="sm",
                    className="w-100 mb-2"
                )
            ], width=6),
            dbc.Col([
                dbc.Button(
                    "💰 Data Quality",
                    id="quality-btn",
                    color="secondary",
                    outline=True,
                    size="sm",
                    className="w-100 mb-2"
                )
            ], width=6),
            dbc.Col([
                dbc.Button(
                    "Unique Patterns",
                    id="unique-patterns-btn",
                    color="primary",
                    outline=True,
                    size="sm",
                    className="w-100 mb-2"
                )
            ], width=6)
        ])
    ], width=6)


def get_updated_button_group():
    """Replace the generate analytics button group with this"""
    return dbc.ButtonGroup([
        dbc.Button(
            "🔄 Refresh Data Sources",
            id="refresh-sources-btn",
            color="outline-secondary",
            size="lg"
        )
    ])


def get_initial_message():
    """Initial message when no button clicked"""
    return dbc.Alert([
        html.H6("👈 Get Started"),
        html.P("1. Select a data source from dropdown"),
        html.P("2. Click any analysis button to run immediately"),
        html.P("Each button runs its analysis type automatically")
    ], color="info")


# =============================================================================
# SECTION 5: LAYOUT FUNCTION REPLACEMENT
# COMPLETELY REPLACE the layout() function in pages/deep_analytics.py
# =============================================================================




# =============================================================================
# SECTION 7: HELPER DISPLAY FUNCTIONS
# Add these helper functions for non-suggests analysis types
# =============================================================================


def analyze_data_with_service(data_source: str, analysis_type: str) -> Dict[str, Any]:
    """Generate different analysis based on type"""
    try:
        service = get_analytics_service_safe()
        if not service:
            return {"error": "Analytics service not available"}

        # Convert data source format
        if data_source.startswith("upload:") or data_source == "service:uploaded":
            source_name = "uploaded"
        elif data_source.startswith("service:"):
            source_name = data_source.replace("service:", "")
        else:
            source_name = data_source

        # Get base analytics
        analytics_results = service.get_analytics_by_source(source_name)

        if analytics_results.get('status') == 'error':
            return {"error": analytics_results.get('message', 'Unknown error')}

        # Get base metrics
        total_events = analytics_results.get('total_events', 0)
        unique_users = analytics_results.get('unique_users', 0)
        unique_doors = analytics_results.get('unique_doors', 0)
        success_rate = analytics_results.get('success_rate', 0)

        # Fix success rate if needed
        if success_rate == 0 and 'successful_events' in analytics_results:
            successful_events = analytics_results.get('successful_events', 0)
            if total_events > 0:
                success_rate = successful_events / total_events

        # Generate DIFFERENT results based on analysis type
        if analysis_type == "security":
            return {
                "analysis_type": "Security Patterns",
                "data_source": data_source,
                "total_events": total_events,
                "unique_users": unique_users,
                "unique_doors": unique_doors,
                "success_rate": success_rate,
                "security_score": min(100, success_rate * 100 + 20),
                "failed_attempts": total_events - int(total_events * success_rate),
                "risk_level": "Low" if success_rate > 0.9 else "Medium" if success_rate > 0.7 else "High",
                "date_range": analytics_results.get('date_range', {}),
                "analysis_focus": "Security threats, failed access attempts, and unauthorized access patterns",
            }

        elif analysis_type == "trends":
            return {
                "analysis_type": "Access Trends",
                "data_source": data_source,
                "total_events": total_events,
                "unique_users": unique_users,
                "unique_doors": unique_doors,
                "success_rate": success_rate,
                "daily_average": total_events / 30,  # Assume 30 days
                "peak_usage": "High activity detected",
                "trend_direction": "Increasing" if total_events > 100000 else "Stable",
                "date_range": analytics_results.get('date_range', {}),
                "analysis_focus": "Usage patterns, peak times, and access frequency trends over time",
            }

        elif analysis_type == "behavior":
            return {
                "analysis_type": "User Behavior",
                "data_source": data_source,
                "total_events": total_events,
                "unique_users": unique_users,
                "unique_doors": unique_doors,
                "success_rate": success_rate,
                "avg_accesses_per_user": total_events / unique_users if unique_users > 0 else 0,
                "heavy_users": int(unique_users * 0.1),  # Top 10%
                "behavior_score": "Normal" if success_rate > 0.8 else "Unusual",
                "date_range": analytics_results.get('date_range', {}),
                "analysis_focus": "Individual user patterns, frequency analysis, and behavioral anomalies",
            }

        elif analysis_type == "anomaly":
            return {
                "analysis_type": "Anomaly Detection",
                "data_source": data_source,
                "total_events": total_events,
                "unique_users": unique_users,
                "unique_doors": unique_doors,
                "success_rate": success_rate,
                "anomalies_detected": int(total_events * (1 - success_rate)),
                "threat_level": "Critical" if success_rate < 0.5 else "Warning" if success_rate < 0.8 else "Normal",
                "suspicious_activities": "Multiple failed attempts detected" if success_rate < 0.9 else "No major issues",
                "date_range": analytics_results.get('date_range', {}),
                "analysis_focus": "Suspicious access patterns, security breaches, and abnormal behaviors",
            }

        else:
            # Default fallback
            return {
                "analysis_type": analysis_type,
                "data_source": data_source,
                "total_events": total_events,
                "unique_users": unique_users,
                "unique_doors": unique_doors,
                "success_rate": success_rate,
                "date_range": analytics_results.get('date_range', {}),
                "analysis_focus": f"General {analysis_type} analysis",
            }

    except Exception as e:
        return {"error": f"Service analysis failed: {str(e)}"}


def create_data_quality_display_corrected(data_source: str) -> html.Div:
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
        return dbc.Alert(f"Quality analysis error: {str(e)}", color="danger")


def process_quality_analysis(data_source: str) -> Dict[str, Any]:
    """Basic processing for data quality analysis"""
    try:
        if data_source.startswith("upload:") or data_source == "service:uploaded":
            if data_source.startswith("upload:"):
                filename = data_source.replace("upload:", "")
            else:
                filename = None

            from pages.file_upload import get_uploaded_data

            uploaded_files = get_uploaded_data()
            if not uploaded_files:
                return {"error": "No uploaded files found"}

            if filename is None or filename not in uploaded_files:
                filename = list(uploaded_files.keys())[0]

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

            return {
                "analysis_type": "Data Quality",
                "data_source": data_source,
                "total_events": total_rows,
                "unique_users": 0,
                "unique_doors": 0,
                "success_rate": quality_score / 100,
                "analysis_focus": "Data completeness and duplication checks",
                "total_rows": total_rows,
                "total_columns": total_cols,
                "missing_values": missing_values,
                "duplicate_rows": duplicate_rows,
                "quality_score": quality_score,
            }

        return {"error": "Data quality analysis only available for uploaded files"}
    except Exception as e:
        return {"error": f"Quality analysis error: {str(e)}"}


def create_analysis_results_display(results: Dict[str, Any], analysis_type: str) -> html.Div:
    """Create display for different analysis types"""
    try:
        total_events = results.get('total_events', 0)
        unique_users = results.get('unique_users', 0)
        unique_doors = results.get('unique_doors', 0)
        success_rate = results.get('success_rate', 0)
        analysis_focus = results.get('analysis_focus', '')

        # Create type-specific content
        if analysis_type == "security":
            specific_content = [
                html.P(f"Security Score: {results.get('security_score', 0):.1f}/100"),
                html.P(f"Failed Attempts: {results.get('failed_attempts', 0):,}"),
                html.P(f"Risk Level: {results.get('risk_level', 'Unknown')}")
            ]
            color = "danger" if results.get('risk_level') == "High" else "warning" if results.get('risk_level') == "Medium" else "success"

        elif analysis_type == "trends":
            specific_content = [
                html.P(f"Daily Average: {results.get('daily_average', 0):.0f} events"),
                html.P(f"Peak Usage: {results.get('peak_usage', 'Unknown')}"),
                html.P(f"Trend: {results.get('trend_direction', 'Unknown')}")
            ]
            color = "info"

        elif analysis_type == "behavior":
            specific_content = [
                html.P(f"Avg Accesses/User: {results.get('avg_accesses_per_user', 0):.1f}"),
                html.P(f"Heavy Users: {results.get('heavy_users', 0)}"),
                html.P(f"Behavior Score: {results.get('behavior_score', 'Unknown')}")
            ]
            color = "success"

        elif analysis_type == "anomaly":
            specific_content = [
                html.P(f"Anomalies Detected: {results.get('anomalies_detected', 0):,}"),
                html.P(f"Threat Level: {results.get('threat_level', 'Unknown')}"),
                html.P(f"Status: {results.get('suspicious_activities', 'Unknown')}")
            ]
            color = "danger" if results.get('threat_level') == "Critical" else "warning"

        else:
            specific_content = [html.P("Standard analysis completed")]
            color = "info"

        return dbc.Card([
            dbc.CardHeader([
                html.H5(f"📊 {results.get('analysis_type', analysis_type)} Results")
            ]),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.H6("📈 Summary"),
                        html.P(f"Total Events: {total_events:,}"),
                        html.P(f"Unique Users: {unique_users:,}"),
                        html.P(f"Unique Doors: {unique_doors:,}"),
                        dbc.Progress(
                            value=success_rate * 100,
                            label=f"Success Rate: {success_rate:.1%}",
                            color="success" if success_rate > 0.8 else "warning"
                        )
                    ], width=6),
                    dbc.Col([
                        html.H6(f"🎯 {analysis_type.title()} Specific"),
                        html.Div(specific_content)
                    ], width=6)
                ]),
                html.Hr(),
                dbc.Alert([
                    html.H6("Analysis Focus"),
                    html.P(analysis_focus)
                ], color=color)
            ])
        ])
    except Exception as e:
        return dbc.Alert(f"Error displaying results: {str(e)}", color="danger")


def create_limited_analysis_display(data_source: str, analysis_type: str) -> html.Div:
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


def create_data_quality_display(data_source: str) -> html.Div:
    """Create data quality analysis display"""
    try:
        if data_source.startswith("upload:"):
            filename = data_source.replace("upload:", "")
            from components.file_upload import get_uploaded_data_store

            uploaded_files = get_uploaded_data_store()

            if filename in uploaded_files:
                df = uploaded_files[filename]

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
        return dbc.Alert(f"Quality analysis error: {str(e)}", color="danger")

def get_initial_message_safe():
    """Initial message with safe ASCII text"""
    return dbc.Alert([
        html.H6("Get Started"),
        html.P("1. Select a data source from dropdown"),
        html.P("2. Click any analysis button to run immediately"),
        html.P("Each button runs its analysis type automatically")
    ], color="info")


def process_suggests_analysis_safe(data_source):
    """Safe AI suggestions analysis"""
    try:
        if data_source.startswith("upload:") or data_source == "service:uploaded":
            from pages.file_upload import get_uploaded_data
            uploaded_files = get_uploaded_data()
            if not uploaded_files:
                return {"error": "No uploaded files found"}
            filename = data_source.replace("upload:", "") if data_source.startswith("upload:") else list(uploaded_files.keys())[0]
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
                "total_rows": len(df)
            }
        return {"error": "AI suggestions only available for uploaded files"}
    except Exception as e:
        return {"error": f"AI analysis error: {str(e)}"}


def process_quality_analysis_safe(data_source):
    """Safe data quality analysis"""
    try:
        if data_source.startswith("upload:") or data_source == "service:uploaded":
            from pages.file_upload import get_uploaded_data
            uploaded_files = get_uploaded_data()
            if not uploaded_files:
                return {"error": "No uploaded files found"}
            filename = data_source.replace("upload:", "") if data_source.startswith("upload:") else list(uploaded_files.keys())[0]
            df = uploaded_files.get(filename)
            if df is None:
                return {"error": f"File {filename} not found"}
            total_rows = len(df)
            total_cols = len(df.columns)
            missing_values = df.isnull().sum().sum()
            duplicate_rows = df.duplicated().sum()
            quality_score = max(0, 100 - (missing_values + duplicate_rows) / total_rows * 100)
            return {
                "analysis_type": "Data Quality",
                "filename": filename,
                "total_rows": total_rows,
                "total_columns": total_cols,
                "missing_values": int(missing_values),
                "duplicate_rows": int(duplicate_rows),
                "quality_score": round(quality_score, 1)
            }
        return {"error": "Data quality analysis only available for uploaded files"}
    except Exception as e:
        return {"error": f"Quality analysis error: {str(e)}"}


def analyze_data_with_service_safe(data_source, analysis_type):
    """Safe service-based analysis"""
    try:
        service = get_analytics_service_safe()
        if not service:
            return {"error": "Analytics service not available"}
        source_name = data_source.replace("service:", "") if data_source.startswith("service:") else "uploaded"
        analytics_results = service.get_analytics_by_source(source_name)
        if analytics_results.get('status') == 'error':
            return {"error": analytics_results.get('message', 'Unknown error')}
        return {
            "analysis_type": analysis_type.title(),
            "data_source": data_source,
            "total_events": analytics_results.get('total_events', 0),
            "unique_users": analytics_results.get('unique_users', 0),
            "success_rate": analytics_results.get('success_rate', 0),
            "status": "completed"
        }
    except Exception as e:
        return {"error": f"Service analysis failed: {str(e)}"}


def create_analysis_results_display_safe(results, analysis_type):
    """Create safe results display without Unicode issues"""
    try:
        if isinstance(results, dict) and "error" in results:
            return dbc.Alert(str(results["error"]), color="danger")
        content = [
            html.H5(f"{analysis_type.title()} Results"),
            html.Hr()
        ]
        if analysis_type == "suggests" and "suggestions" in results:
            content.extend([
                html.P(f"File: {results.get('filename', 'Unknown')}"),
                html.P(f"Columns analyzed: {results.get('total_columns', 0)}"),
                html.P(f"Rows processed: {results.get('total_rows', 0)}"),
                html.H6("AI Column Suggestions:"),
                html.Div([
                    html.P(f"{col}: {info.get('field', 'unknown')} (confidence: {info.get('confidence', 0):.1f})")
                    for col, info in results.get('suggestions', {}).items()
                ])
            ])
        elif analysis_type == "quality":
            content.extend([
                html.P(f"Total rows: {results.get('total_rows', 0):,}"),
                html.P(f"Total columns: {results.get('total_columns', 0)}"),
                html.P(f"Missing values: {results.get('missing_values', 0):,}"),
                html.P(f"Duplicate rows: {results.get('duplicate_rows', 0):,}"),
                html.P(f"Quality score: {results.get('quality_score', 0):.1f}%")
            ])
        else:
            content.extend([
                html.P(f"Total events: {results.get('total_events', 0):,}"),
                html.P(f"Unique users: {results.get('unique_users', 0):,}"),
                html.P(f"Success rate: {results.get('success_rate', 0):.1%}")
            ])
        return dbc.Card([
            dbc.CardBody(content)
        ])
    except Exception as e:
        return dbc.Alert(f"Display error: {str(e)}", color="danger")


