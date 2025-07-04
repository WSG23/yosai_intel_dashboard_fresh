from dataclasses import dataclass
from typing import Dict, Any, List

__all__ = ["AnomalyAnalysis"]


@dataclass
class AnomalyAnalysis:
    """Comprehensive anomaly analysis result"""

    total_anomalies: int
    severity_distribution: Dict[str, int]
    detection_summary: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    recommendations: List[str]
