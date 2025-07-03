import logging
from typing import Dict, Any, List, Tuple

import pandas as pd
from dash import html
import dash_bootstrap_components as dbc

from services.ai_suggestions import generate_column_suggestions
from utils.unicode_handler import sanitize_unicode_input, safe_format_number

logger = logging.getLogger(__name__)


def get_display_title(analysis_type: str) -> str:
    """Return a human friendly title for an analysis type."""
    title_map = {
        "security": "Security Results",
        "trends": "Trends Results",
        "behavior": "Behavior Results",
        "anomaly": "Anomaly Results",
    }
    return title_map.get(analysis_type.lower(), f"{analysis_type.title()} Results")


def build_ai_suggestions(df: pd.DataFrame) -> Tuple[List[Dict[str, Any]], float, int]:
    """Generate processed AI column suggestions for a dataframe."""
    try:
        suggestions = generate_column_suggestions(list(df.columns))
    except Exception as e:  # pragma: no cover - fallback
        logger.exception("AI suggestions failed: %s", e)
        suggestions = {col: {"field": "", "confidence": 0.0} for col in df.columns}

    processed: List[Dict[str, Any]] = []
    total_conf = 0.0
    confident = 0
    for column, info in suggestions.items():
        field = info.get("field", "")
        confidence = info.get("confidence", 0.0)

        status = "🟢 High" if confidence >= 0.7 else "🟡 Medium" if confidence >= 0.4 else "🔴 Low"
        try:
            sample = df[column].dropna().head(3).astype(str).tolist()
        except Exception:  # pragma: no cover - defensive
            sample = ["N/A"]

        processed.append({
            "column": column,
            "suggested_field": field if field else "No suggestion",
            "confidence": confidence,
            "status": status,
            "sample_data": sample,
        })

        total_conf += confidence
        if confidence >= 0.6:
            confident += 1

    avg_conf = total_conf / len(processed) if processed else 0.0
    return processed, avg_conf, confident


def extract_counts(results: Dict[str, Any]) -> Dict[str, int]:
    """Extract common count metrics from analysis results."""
    total_events = results.get("total_events", 0)

    users_raw = results.get("unique_users", 0)
    unique_users = len(users_raw) if isinstance(users_raw, (set, list)) else int(users_raw or 0)

    doors_raw = results.get("unique_doors", 0)
    unique_doors = len(doors_raw) if isinstance(doors_raw, (set, list)) else int(doors_raw or 0)

    success_rate = results.get("success_rate", 0)
    if success_rate == 0:
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


def extract_security_metrics(results: Dict[str, Any]) -> Dict[str, Any]:
    """Extract security specific metrics from results."""
    raw = results.get("security_score", {})
    if hasattr(raw, "score"):
        score_val = float(raw.score)
        risk_level = raw.threat_level.title()
    elif isinstance(raw, dict):
        score_val = float(raw.get("score", 0.0))
        risk_level = raw.get("threat_level", "unknown").title()
    else:
        score_val = float(raw) if raw else 0.0
        risk_level = "Unknown"

    failed_attempts = results.get("failed_attempts", 0) or results.get("failed_events", 0)
    return {
        "score": score_val,
        "risk_level": risk_level,
        "failed_attempts": failed_attempts,
    }


def render_results_card(results: Dict[str, Any], analysis_type: str) -> dbc.Card | dbc.Alert:
    """Render a results card for a given analysis type."""
    try:
        counts = extract_counts(results)
        total_events = counts["total_events"]
        unique_users = counts["unique_users"]
        unique_doors = counts["unique_doors"]
        success_rate = counts["success_rate"]
        analysis_focus = results.get("analysis_focus", "")

        if analysis_type == "security":
            sec = extract_security_metrics(results)
            specific_content = [
                html.P(f"Security Score: {sec['score']:.1f}/100"),
                html.P(f"Failed Attempts: {sec['failed_attempts']:,}"),
                html.P(f"Risk Level: {sec['risk_level']}")
            ]
            color = "danger" if sec["risk_level"] == "High" else "warning" if sec["risk_level"] == "Medium" else "success"
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
                html.P(f"Threat Level: {results.get('threat_level', 'Unknown')}") ,
                html.P(f"Status: {results.get('suspicious_activities', 'Unknown')}")
            ]
            color = "danger" if results.get("threat_level") == "Critical" else "warning"
        else:
            specific_content = [html.P("Standard analysis completed")]
            color = "info"

        title_safe = sanitize_unicode_input(get_display_title(analysis_type))
        events_safe = safe_format_number(total_events)
        users_safe = safe_format_number(unique_users)
        doors_safe = safe_format_number(unique_doors)

        return dbc.Card([
            dbc.CardHeader([html.H5(f"\U0001F4CA {title_safe}")]),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.H6("\U0001F4C8 Summary"),
                        html.P(f"Total Events: {events_safe}"),
                        html.P(f"Unique Users: {users_safe}"),
                        html.P(f"Unique Doors: {doors_safe}"),
                        dbc.Progress(
                            value=success_rate * 100,
                            label=f"Success Rate: {success_rate:.1%}",
                            color="success" if success_rate > 0.8 else "warning",
                        ),
                    ], width=6),
                    dbc.Col([
                        html.H6(f"\U0001F3AF {analysis_type.title()} Specific"),
                        html.Div(specific_content),
                    ], width=6),
                ]),
                html.Hr(),
                dbc.Alert([
                    html.H6("Analysis Focus"),
                    html.P(analysis_focus),
                ], color=color),
            ]),
        ])
    except Exception as e:  # pragma: no cover - defensive
        logger.exception("Error displaying results: %s", e)
        return dbc.Alert(f"Error displaying results: {str(e)}", color="danger")


__all__ = [
    "build_ai_suggestions",
    "extract_counts",
    "extract_security_metrics",
    "render_results_card",
    "get_display_title",
]
