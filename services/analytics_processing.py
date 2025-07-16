import logging
from typing import Any, Dict

import dash_bootstrap_components as dbc
import pandas as pd
from dash import html

from core.unicode import safe_format_number
from core.unicode_utils import sanitize_for_utf8
from services import get_analytics_service
from services.data_enhancer import get_ai_column_suggestions as generate_column_suggestions
from services.upload_data_service import get_uploaded_data
from services.interfaces import get_upload_data_service
from utils.preview_utils import serialize_dataframe_preview

logger = logging.getLogger(__name__)


def process_suggests_analysis(data_source: str) -> Dict[str, Any]:
    """Process AI suggestions analysis for the selected data source."""
    try:
        logger.info("🔍 Processing suggests analysis for: %s", data_source)
        if not data_source or data_source == "none":
            return {"error": "No data source selected"}

        if data_source.startswith("upload:") or data_source == "service:uploaded":
            filename = None
            if data_source.startswith("upload:"):
                filename = data_source.replace("upload:", "")
            uploaded_files = get_uploaded_data(get_upload_data_service())
            if not uploaded_files:
                return {"error": "No uploaded files found"}
            if filename is None or filename not in uploaded_files:
                filename = list(uploaded_files.keys())[0]
            df = uploaded_files[filename]

            try:
                suggestions = generate_column_suggestions(list(df.columns))
                processed = []
                total_conf = 0
                confident = 0
                for column, sugg in suggestions.items():
                    field = sugg.get("field", "")
                    conf = sugg.get("confidence", 0.0)
                    status = (
                        "🟢 High"
                        if conf >= 0.7
                        else "🟡 Medium"
                        if conf >= 0.4
                        else "🔴 Low"
                    )
                    try:
                        sample_data = df[column].dropna().head(3).astype(str).tolist()
                    except Exception:
                        sample_data = ["N/A"]
                    processed.append(
                        {
                            "column": column,
                            "suggested_field": field or "No suggestion",
                            "confidence": conf,
                            "status": status,
                            "sample_data": sample_data,
                        }
                    )
                    total_conf += conf
                    if conf >= 0.6:
                        confident += 1
                avg_conf = total_conf / len(suggestions) if suggestions else 0
                preview = serialize_dataframe_preview(df)
                return {
                    "filename": filename,
                    "total_columns": len(df.columns),
                    "total_rows": len(df),
                    "suggestions": processed,
                    "avg_confidence": avg_conf,
                    "confident_mappings": confident,
                    "data_preview": preview,
                    "column_names": list(df.columns),
                }
            except Exception as exc:
                logger.exception("AI suggestions failed: %s", exc)
                return {"error": f"AI suggestions failed: {exc}"}
        return {
            "error": f"Suggests analysis not available for data source: {data_source}"
        }
    except Exception as exc:
        logger.exception("Failed to process suggests: %s", exc)
        return {"error": f"Failed to process suggests: {exc}"}


def create_suggests_display(
    suggests_data: Dict[str, Any]
) -> html.Div | dbc.Card | dbc.Alert:
    """Create suggests analysis display components."""
    if "error" in suggests_data:
        return dbc.Alert(f"Error: {suggests_data['error']}", color="danger")
    try:
        filename = suggests_data.get("filename", "Unknown")
        suggestions = suggests_data.get("suggestions", [])
        avg_confidence = suggests_data.get("avg_confidence", 0)
        confident_mappings = suggests_data.get("confident_mappings", 0)
        total_columns = suggests_data.get("total_columns", 0)
        total_rows = suggests_data.get("total_rows", 0)

        summary_card = dbc.Card(
            [
                dbc.CardHeader([html.H5(f"🤖 AI Column Mapping Analysis - {filename}")]),
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
                                            color="success"
                                            if avg_confidence >= 0.7
                                            else "warning"
                                            if avg_confidence >= 0.4
                                            else "danger",
                                        ),
                                    ],
                                    width=4,
                                ),
                                dbc.Col(
                                    [
                                        html.H6("Confident Mappings"),
                                        html.H3(
                                            f"{confident_mappings}/{total_columns}",
                                            className="text-success"
                                            if confident_mappings >= total_columns * 0.7
                                            else "text-warning",
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

        if suggestions:
            table_rows = [
                html.Tr(
                    [
                        html.Td(s["column"]),
                        html.Td(s["suggested_field"]),
                        html.Td(
                            dbc.Progress(
                                value=s["confidence"] * 100,
                                label=f"{s['confidence']:.1%}",
                                color="success"
                                if s["confidence"] >= 0.7
                                else "warning"
                                if s["confidence"] >= 0.4
                                else "danger",
                            )
                        ),
                        html.Td(s["status"]),
                        html.Td(
                            html.Small(
                                str(s["sample_data"][:2]), className="text-muted"
                            )
                        ),
                    ]
                )
                for s in suggestions
            ]
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
    except Exception as exc:
        logger.exception("Error creating suggests display: %s", exc)
        return dbc.Alert(f"Error creating display: {exc}", color="danger")


def process_quality_analysis(data_source: str) -> Dict[str, Any]:
    """Basic processing for data quality analysis."""
    try:
        if data_source.startswith("upload:") or data_source == "service:uploaded":
            filename = None
            if data_source.startswith("upload:"):
                filename = data_source.replace("upload:", "")
            uploaded_files = get_uploaded_data(get_upload_data_service())
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
    except Exception as exc:
        logger.exception("Quality analysis processing error: %s", exc)
        return {"error": f"Quality analysis error: {exc}"}


def create_data_quality_display(data_source: str) -> html.Div | dbc.Card | dbc.Alert:
    """Create data quality analysis display."""
    try:
        if data_source.startswith("upload:"):
            filename = data_source.replace("upload:", "")
            uploaded_files = get_uploaded_data(get_upload_data_service())
            if filename in uploaded_files:
                df = uploaded_files[filename]
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
    except Exception as exc:
        logger.exception("Quality analysis error: %s", exc)
        return dbc.Alert(f"Quality analysis error: {exc}", color="danger")


def analyze_data_with_service(data_source: str, analysis_type: str) -> Dict[str, Any]:
    """Generate analysis using the analytics service with chunked processing."""
    try:
        service = get_analytics_service()
        if not service:
            return {"error": "Analytics service not available"}
        if data_source.startswith("upload:") or data_source == "service:uploaded":
            filename = None
            if data_source.startswith("upload:"):
                filename = data_source.replace("upload:", "")
            uploaded_files = get_uploaded_data(get_upload_data_service())
            if not uploaded_files:
                return {"error": "No uploaded files found"}
            if filename is None or filename not in uploaded_files:
                filename = list(uploaded_files.keys())[0]
            df = uploaded_files.get(filename)
            if df is None:
                return {"error": f"File {filename} not found"}
        else:
            df, _ = service.data_loader.get_processed_database()
            if df.empty:
                return {"error": "No data available"}
        analysis_types = [analysis_type]
        return service.analyze_with_chunking(df, analysis_types)
    except Exception as exc:
        logger.exception("Analysis failed: %s", exc)
        return {"error": f"Analysis failed: {exc}"}


# Helper extraction functions for results processing


def _extract_counts(results: Dict[str, Any]) -> Dict[str, int | float]:
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
    top_threats: list[str] = []
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
    """Create display for different analysis types."""
    try:
        counts = _extract_counts(results)
        total_events = counts["total_events"]
        unique_users = counts["unique_users"]
        unique_doors = counts["unique_doors"]
        success_rate = counts["success_rate"]
        analysis_focus = results.get("analysis_focus", "")

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
                else "warning"
                if sec_metrics["risk_level"] == "Medium"
                else "success"
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

        title_safe = sanitize_for_utf8(analysis_type.title() + " Results")
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
                                            color="success"
                                            if success_rate > 0.8
                                            else "warning",
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
    except Exception as exc:
        logger.exception("Error displaying results: %s", exc)
        return dbc.Alert(f"Error displaying results: {exc}", color="danger")


__all__ = [
    "process_suggests_analysis",
    "create_suggests_display",
    "process_quality_analysis",
    "create_data_quality_display",
    "analyze_data_with_service",
    "create_analysis_results_display",
]
