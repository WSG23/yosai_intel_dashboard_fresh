"""Risk scoring utilities with environmental context awareness."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

import pandas as pd

from . import feature_extraction


@dataclass
class RiskScoreResult:
    score: float
    level: str


@dataclass
class AnomalyAnalysis:
    total_anomalies: int
    severity_distribution: Dict[str, int]
    detection_summary: Dict[str, int]
    risk_assessment: Dict[str, float]
    recommendations: List[str]


@dataclass
class SecurityAssessment:
    overall_score: float
    risk_level: str
    confidence_interval: tuple
    threat_indicators: List[str]
    pattern_analysis: Dict[str, float]
    recommendations: List[str]


@dataclass
class BehaviorAnalysis:
    total_users_analyzed: int
    high_risk_users: int
    global_patterns: Dict[str, float]
    insights: List[str]
    recommendations: List[str]


# ---------------------------------------------------------------------------
# Core utilities
# ---------------------------------------------------------------------------


def _risk_level(score: float) -> str:
    if score >= 75:
        return "critical"
    if score >= 50:
        return "high"
    if score >= 25:
        return "medium"
    return "low"


def _context_modifier(context: Optional[Dict[str, object]]) -> float:
    if not context:
        return 1.0
    modifier = 1.0
    weather = context.get("weather", {}) if isinstance(context, dict) else {}
    condition = getattr(weather, "get", lambda *_: None)("condition")
    if condition in {"storm", "extreme"}:
        modifier += 0.1
    events = context.get("events", []) if isinstance(context, dict) else []
    if events:
        modifier += min(0.05 * len(events), 0.2)
    social = context.get("social", {}) if isinstance(context, dict) else {}
    sentiment = getattr(social, "get", lambda *_: None)("sentiment")
    if sentiment is not None:
        modifier += 0.1 if sentiment < 0 else -0.05
    return modifier


def _make_result(score: float, level: str) -> RiskScoreResult:
    """Return a :class:`RiskScoreResult` with the given values."""
    return RiskScoreResult(score=score, level=level)


def calculate_risk_score(
    anomaly_score: float,
    pattern_score: float,
    behavior_score: float,
    *,
    context: Optional[Dict[str, object]] = None,
) -> RiskScoreResult:
    """Combine numeric risk components and apply context modifiers."""

    base = round((anomaly_score + pattern_score + behavior_score) / 3, 2)
    final = round(base * _context_modifier(context), 2)
    return _make_result(final, _risk_level(final))


def combine_risk_factors(
    anomaly: AnomalyAnalysis,
    patterns: SecurityAssessment,
    behavior: BehaviorAnalysis,
    *,
    context: Optional[Dict[str, object]] = None,
) -> RiskScoreResult:
    """Aggregate analysis components into a single risk score."""

    anomaly_score = anomaly.risk_assessment.get("risk_score", 0) * 100
    pattern_score = patterns.overall_score
    if behavior.total_users_analyzed:
        behavior_ratio = behavior.high_risk_users / behavior.total_users_analyzed
    else:
        behavior_ratio = 0
    behavior_score = behavior_ratio * 100
    return calculate_risk_score(
        anomaly_score, pattern_score, behavior_score, context=context
    )


def score_events(
    df: pd.DataFrame, *, context: Optional[Dict[str, object]] = None
) -> RiskScoreResult:
    """Score raw event data using simple heuristics and context."""

    features = feature_extraction.extract_event_features(df)
    total = len(features)
    denied = int(features["access_denied"].sum())
    anomaly_score = (denied / total) * 100 if total else 0
    return calculate_risk_score(anomaly_score, 0, 0, context=context)
