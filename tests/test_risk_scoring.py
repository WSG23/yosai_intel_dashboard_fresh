from yosai_intel_dashboard.src.core.imports.resolver import safe_import
# Provide minimal dash stub if dash is unavailable
import sys

if "dash" not in sys.modules:
    from tests.stubs import dash as dash_stub

    safe_import('dash', dash_stub  # type: ignore)
    safe_import('dash.html', dash_stub.html  # type: ignore)
    safe_import('dash.dcc', dash_stub.dcc  # type: ignore)
    safe_import('dash.dependencies', dash_stub.dependencies  # type: ignore)
    safe_import('dash._callback', dash_stub._callback  # type: ignore)

import importlib.util
import types
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

# Load feature_extraction module directly to avoid heavy package import
FEATURE_PATH = (
    Path(__file__).resolve().parents[1] / "analytics" / "feature_extraction.py"
)
spec_feat = importlib.util.spec_from_file_location("feature_extraction", FEATURE_PATH)
feature_mod = importlib.util.module_from_spec(spec_feat)
spec_feat.loader.exec_module(feature_mod)

analytics_stub = types.ModuleType("analytics")
analytics_stub.feature_extraction = feature_mod
analytics_stub.__path__ = [str(Path(__file__).resolve().parents[1] / "analytics")]
safe_import('analytics', analytics_stub)
safe_import('services.analytics.feature_extraction', feature_mod)

# Stub dependent modules to avoid heavy imports
anom_types = types.ModuleType("services.analytics.anomaly_detection.types")


@dataclass
class AnomalyAnalysis:
    total_anomalies: int
    severity_distribution: dict
    detection_summary: dict
    risk_assessment: dict
    recommendations: list


anom_types.AnomalyAnalysis = AnomalyAnalysis
safe_import('services.analytics.anomaly_detection.types', anom_types)

sec_analyzer = types.ModuleType("services.analytics.security_patterns.analyzer")


@dataclass
class SecurityAssessment:
    overall_score: float
    risk_level: str
    confidence_interval: tuple
    threat_indicators: list
    pattern_analysis: dict
    recommendations: list


sec_analyzer.SecurityAssessment = SecurityAssessment
safe_import('services.analytics.security_patterns.analyzer', sec_analyzer)

behav_mod = types.ModuleType("services.analytics.user_behavior")


@dataclass
class BehaviorAnalysis:
    total_users_analyzed: int
    high_risk_users: int
    global_patterns: dict
    insights: list
    recommendations: list


behav_mod.BehaviorAnalysis = BehaviorAnalysis
safe_import('services.analytics.user_behavior', behav_mod)

RISK_PATH = Path(__file__).resolve().parents[1] / "analytics" / "risk_scoring.py"
spec_risk = importlib.util.spec_from_file_location("services.analytics.risk_scoring", RISK_PATH)
risk_mod = importlib.util.module_from_spec(spec_risk)
safe_import('services.analytics.risk_scoring', risk_mod)
spec_risk.loader.exec_module(risk_mod)

AnomalyAnalysis = (
    risk_mod.AnomalyAnalysis if hasattr(risk_mod, "AnomalyAnalysis") else None
)
RiskScoreResult = risk_mod.RiskScoreResult
calculate_risk_score = risk_mod.calculate_risk_score
combine_risk_factors = risk_mod.combine_risk_factors
score_events = risk_mod.score_events
SecurityAssessment = risk_mod.SecurityAssessment
BehaviorAnalysis = risk_mod.BehaviorAnalysis

# Provide minimal dash stub if dash is unavailable
if "dash" not in sys.modules:
    from tests.stubs import dash as dash_stub

    safe_import('dash', dash_stub  # type: ignore)
    safe_import('dash.html', dash_stub.html  # type: ignore)
    safe_import('dash.dcc', dash_stub.dcc  # type: ignore)
    safe_import('dash.dependencies', dash_stub.dependencies  # type: ignore)
    safe_import('dash._callback', dash_stub._callback  # type: ignore)


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


def test_score_events_from_dataframe():
    df = pd.DataFrame(
        {
            "timestamp": ["2024-01-01 23:00:00", "2024-01-02 09:00:00"],
            "person_id": ["u1", "u1"],
            "door_id": ["d1", "d2"],
            "access_result": ["Denied", "Granted"],
        }
    )
    result = score_events(df)
    assert isinstance(result, RiskScoreResult)
