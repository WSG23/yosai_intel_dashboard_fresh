from dataclasses import dataclass
from typing import Dict, Any, List
from datetime import datetime

__all__ = ["ThreatIndicator"]

@dataclass
class ThreatIndicator:
    """Individual threat indicator used by security analysis"""

    threat_type: str
    severity: str  # 'critical', 'high', 'medium', 'low'
    confidence: float  # 0.0 to 1.0
    description: str
    evidence: Dict[str, Any]
    timestamp: datetime
    affected_entities: List[str]
