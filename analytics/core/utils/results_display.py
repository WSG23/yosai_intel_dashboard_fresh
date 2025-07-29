# from __future__ import annotations

"""Utilities for building analysis result displays."""

from typing import Any, Dict

import dash_bootstrap_components as dbc
from dash import html

from core.unicode import safe_format_number, sanitize_for_utf8

__all__ = [
    "_extract_counts",
    "_extract_security_metrics",
    "_extract_enhanced_security_details",
    "create_analysis_results_display",
    "create_analysis_results_display_safe",
]


def _extract_counts(results: Dict[str, Any]) -> Dict[str, int | float]:
    total_events = results.get("total_events", 0)

    def _normalize_count(value: Any) -> int:
        if value is None:
            return 0
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return int(value)
        if hasattr(value, "__len__") and not isinstance(value, (str, bytes)):
            try:
                return len(value)  # type: ignore[arg-type]
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
                                            color="success" if success_rate > 0.8 else "warning",
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
    except Exception as exc:  # pragma: no cover - best effort
        import logging

        logging.getLogger(__name__).exception("Error displaying results: %s", exc)
        return dbc.Alert(f"Error displaying results: {exc}", color="danger")


def create_analysis_results_display_safe(
    results: Dict[str, Any], analysis_type: str
) -> html.Div | dbc.Card | dbc.Alert:
    """Safer variant of :func:`create_analysis_results_display`."""
    return create_analysis_results_display(results, analysis_type)

