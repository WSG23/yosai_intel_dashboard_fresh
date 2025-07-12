# Provide minimal dash stub if dash is unavailable
import sys

if "dash" not in sys.modules:
    from tests.stubs import dash as dash_stub

    sys.modules["dash"] = dash_stub  # type: ignore
    sys.modules["dash.html"] = dash_stub.html  # type: ignore
    sys.modules["dash.dcc"] = dash_stub.dcc  # type: ignore
    sys.modules["dash.dependencies"] = dash_stub.dependencies  # type: ignore
    sys.modules["dash._callback"] = dash_stub._callback  # type: ignore

from analytics.anomaly_detection.types import AnomalyAnalysis
from analytics.risk_scoring import (
    RiskScoreResult,
    calculate_risk_score,
    combine_risk_factors,
)
from analytics.security_patterns.analyzer import SecurityAssessment
from analytics.user_behavior import BehaviorAnalysis

# Provide minimal dash stub if dash is unavailable
if "dash" not in sys.modules:
    from tests.stubs import dash as dash_stub

    sys.modules["dash"] = dash_stub  # type: ignore
    sys.modules["dash.html"] = dash_stub.html  # type: ignore
    sys.modules["dash.dcc"] = dash_stub.dcc  # type: ignore
    sys.modules["dash.dependencies"] = dash_stub.dependencies  # type: ignore
    sys.modules["dash._callback"] = dash_stub._callback  # type: ignore


def test_calculate_risk_score_numeric():
    result = calculate_risk_score(50, 20, 30)
    assert isinstance(result, RiskScoreResult)
    assert result.score == 33.33
    assert result.level == "medium"


def test_combine_risk_factors():
    anomaly = AnomalyAnalysis(
        total_anomalies=2,
        severity_distribution={"high": 1, "medium": 1},
        detection_summary={},
        risk_assessment={"risk_level": "high", "risk_score": 0.6},
        recommendations=[],
    )
    patterns = SecurityAssessment(
        overall_score=70,
        risk_level="medium",
        confidence_interval=(50.0, 90.0),
        threat_indicators=[],
        pattern_analysis={},
        recommendations=[],
    )
    behavior = BehaviorAnalysis(
        total_users_analyzed=10,
        high_risk_users=2,
        global_patterns={},
        insights=[],
        recommendations=[],
    )
    result = combine_risk_factors(anomaly, patterns, behavior)
    assert result.level in {"low", "medium", "high", "critical"}
