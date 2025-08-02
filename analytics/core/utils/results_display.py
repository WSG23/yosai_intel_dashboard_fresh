"""Utilities for presenting analytics results in user interfaces."""

from __future__ import annotations

import json
from typing import Any, Mapping, Sequence, cast

import pandas as pd

__all__ = [
    "create_analysis_results_display",
    "format_analytics_summary",
    "generate_charts",
    "export_results",
    "_extract_enhanced_security_details",
]


# ---------------------------------------------------------------------------
def create_analysis_results_display(
    results: Mapping[str, Any] | pd.DataFrame,
    output_format: str = "html",
) -> Any:
    """Create a visual representation of analytics results.

    Parameters
    ----------
    results:
        Aggregated analytics results as a mapping or dataframe.
    output_format:
        Format for the output. ``"security"`` renders a security summary card.
        ``"html"`` returns a generic card. ``"json"`` returns a JSON string.

    Returns
    -------
    Any
        A Dash card or formatted string depending on ``output_format``.
    """

    if output_format == "json":
        if isinstance(results, pd.DataFrame):
            return results.to_json(orient="records")
        return json.dumps(dict(results))

    try:
        import dash_bootstrap_components as dbc
    except Exception as exc:  # pragma: no cover - handled in tests
        raise ImportError(
            "dash_bootstrap_components is required for card output"
        ) from exc

    if output_format == "security":
        details = _extract_enhanced_security_details(results)
        header_text = "Security Results"
        header = dbc.CardHeader(header_text)
        total_events = details.get("total_events", results.get("total_events", 0))
        threat_level = results.get("security_score", {}).get("threat_level", "unknown")
        lines = [
            f"Total events: {total_events}",
            f"Unique users: {results.get('unique_users', 0)}",
            f"Unique doors: {results.get('unique_doors', 0)}",
            f"Successful events: {results.get('successful_events', 0)}",
            f"Failed events: {results.get('failed_events', 0)}",
            f"Threat level: {threat_level}",
        ]
        body = dbc.CardBody(lines)

        class DisplayCard(dbc.Card):  # pragma: no cover - simple wrapper
            def __str__(self) -> str:
                return header_text

        return DisplayCard([header, body])

    header_text = "Analysis Results"
    header = dbc.CardHeader(header_text)
    body_lines = [f"{k}: {v}" for k, v in dict(results).items()]
    body = dbc.CardBody(body_lines)

    class DisplayCard(dbc.Card):  # pragma: no cover - simple wrapper
        def __str__(self) -> str:
            return header_text

    return DisplayCard([header, body])


# ---------------------------------------------------------------------------
def format_analytics_summary(data: pd.DataFrame | Mapping[str, Any]) -> str:
    """Format analytics data into a human-readable summary string."""

    if isinstance(data, pd.DataFrame):
        if data.empty:
            raise ValueError("dataframe is empty")
        summary = data.describe(include="all").to_string()
        return summary

    if not isinstance(data, Mapping):
        raise TypeError("data must be a DataFrame or mapping")
    return json.dumps(dict(data), indent=2)


# ---------------------------------------------------------------------------
def generate_charts(analytics_data: pd.DataFrame) -> dict[str, Any]:
    """Generate simple chart-ready data from analytics dataframe.

    The function avoids heavy graphics dependencies by returning numerical
    summaries suitable for downstream charting libraries.
    """

    if not isinstance(analytics_data, pd.DataFrame):
        raise TypeError("analytics_data must be a DataFrame")
    if analytics_data.empty:
        raise ValueError("analytics_data is empty")

    charts: dict[str, Any] = {}
    numeric_cols = analytics_data.select_dtypes(include="number").columns
    for col in numeric_cols:
        charts[col] = analytics_data[col].value_counts().to_dict()
    return charts


# ---------------------------------------------------------------------------
def export_results(
    results: pd.DataFrame | Mapping[str, Any],
    format: str = "pdf",
) -> bytes:
    """Export analysis results in various formats.

    Currently supports ``pdf`` (plain text placeholder), ``csv`` and ``json``.
    """

    if format not in {"pdf", "csv", "json"}:
        raise ValueError("unsupported export format")

    if isinstance(results, pd.DataFrame):
        if results.empty:
            raise ValueError("results dataframe is empty")
        if format == "csv":
            return results.to_csv(index=False).encode()
        if format == "json":
            return results.to_json(orient="records").encode()
        summary = format_analytics_summary(results)
        return summary.encode()

    if not isinstance(results, Mapping):
        raise TypeError("results must be a DataFrame or mapping")

    if format == "json":
        return json.dumps(dict(results)).encode()
    # For PDF or CSV fall back to summary text
    summary = format_analytics_summary(results)
    return summary.encode()


# ---------------------------------------------------------------------------
def _extract_enhanced_security_details(results: Mapping[str, Any]) -> dict[str, Any]:
    """Extract and normalize security specific details from results."""

    threats_data = results.get("threats", [])
    threats = cast(Sequence[Mapping[str, Any]], threats_data)
    severity_rank = {"critical": 3, "high": 2, "medium": 1, "low": 0}

    threat_count = results.get("threat_count") or len(threats)
    critical_threats = results.get("critical_threats") or sum(
        1 for t in threats if str(t.get("severity", "")).lower() == "critical"
    )
    confidence_interval = results.get("confidence_interval", (0.0, 0.0))
    recommendations = results.get("recommendations", [])

    sorted_threats = sorted(
        threats,
        key=lambda t: (
            severity_rank.get(str(t.get("severity", "")).lower(), -1),
            t.get("confidence", 0.0),
        ),
        reverse=True,
    )
    top_threats = []
    for t in sorted_threats[:3]:
        severity = str(t.get("severity", "unknown")).title()
        confidence = int(t.get("confidence", 0.0) * 100)
        description = t.get("description", "")
        top_threats.append(f"{severity} ({confidence}%): {description}")

    return {
        "threat_count": threat_count,
        "critical_threats": critical_threats,
        "confidence_interval": confidence_interval,
        "recommendations": recommendations,
        "top_threats": top_threats,
        "total_events": results.get("total_events", 0),
    }
