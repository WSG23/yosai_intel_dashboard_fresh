from __future__ import annotations

"""Aggregate risk scoring utilities."""

from dataclasses import dataclass
from typing import Optional

import pandas as pd

from .feature_extraction import extract_event_features

from .anomaly_detection.types import AnomalyAnalysis
from .security_patterns.analyzer import SecurityAssessment
from .user_behavior import BehaviorAnalysis


@dataclass
class RiskScoreResult:
    """Result returned by :func:`combine_risk_factors`."""

    score: float  # 0-100 scale
    level: str  # low, medium, high, critical


def _determine_level(score: float) -> str:
    if score >= 75:
        return "critical"
    if score >= 50:
        return "high"
    if score >= 25:
        return "medium"
    return "low"


def calculate_risk_score(
    anomaly_component: float = 0.0,
    pattern_component: float = 0.0,
    behavior_component: float = 0.0,
) -> RiskScoreResult:
    """Combine numeric risk components into a final score."""
    components = [
        max(0.0, min(anomaly_component, 100.0)),
        max(0.0, min(pattern_component, 100.0)),
        max(0.0, min(behavior_component, 100.0)),
    ]
    score = sum(components) / len(components)
    return RiskScoreResult(score=round(score, 2), level=_determine_level(score))


def combine_risk_factors(
    anomaly: Optional[AnomalyAnalysis] = None,
    patterns: Optional[SecurityAssessment] = None,
    behavior: Optional[BehaviorAnalysis] = None,
) -> RiskScoreResult:
    """Combine analysis results from different modules into one score."""
    anomaly_score = 0.0
    if anomaly is not None:
        anomaly_score = float(anomaly.risk_assessment.get("risk_score", 0.0)) * 100

    pattern_score = 0.0
    if patterns is not None:
        pattern_score = max(0.0, 100.0 - float(patterns.overall_score))

    behavior_score = 0.0
    if behavior is not None and behavior.total_users_analyzed:
        ratio = behavior.high_risk_users / behavior.total_users_analyzed
        behavior_score = max(0.0, min(ratio * 100, 100.0))

    return calculate_risk_score(anomaly_score, pattern_score, behavior_score)


def score_events(df: pd.DataFrame) -> RiskScoreResult:
    """Calculate a simple risk score directly from event data."""

    features = extract_event_features(df)
    if features.empty:
        return RiskScoreResult(score=0.0, level="low")

    after_hours_rate = features["is_after_hours"].mean()
    weekend_rate = features["is_weekend"].mean()
    failure_rate = 1 - features["access_granted"].mean()

    user_ratio = features["user_event_count"].max() / len(features)
    door_ratio = features["door_event_count"].max() / len(features)

    score = (
        after_hours_rate * 40
        + weekend_rate * 10
        + failure_rate * 40
        + user_ratio * 5
        + door_ratio * 5
    )

    score = max(0.0, min(score, 100.0))
    return RiskScoreResult(score=round(score, 2), level=_determine_level(score))


__all__ = [
    "RiskScoreResult",
    "calculate_risk_score",
    "combine_risk_factors",
    "score_events",
]
