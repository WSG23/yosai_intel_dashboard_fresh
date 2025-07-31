from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List

from core.security import SecurityLevel, security_auditor
from yosai_intel_dashboard.src.services.security_callback_controller import SecurityEvent, emit_security_event

logger = logging.getLogger(__name__)


class ThreatLevel(Enum):
    """Threat severity levels returned by the ML engine."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SecurityThreat:
    """Represents a detected security threat."""

    threat_type: str
    level: ThreatLevel
    score: float
    metadata: Dict[str, Any]
    timestamp: datetime


class MLSecurityEngine:
    """Asynchronous ML-based security threat detection engine."""

    def __init__(
        self, model: Callable[[List[Dict[str, Any]]], Awaitable[List[Dict[str, Any]]]]
    ):
        self.model = model
        self.logger = logging.getLogger(__name__)

    async def _extract_security_features(
        self, events: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Extract features from raw events for model input."""
        await asyncio.sleep(0)  # allow cooperative scheduling
        return events

    async def _run_threat_detection_model(
        self, features: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Run the underlying ML model to detect threats."""
        return await self.model(features)

    async def analyze_security_events(
        self, events: List[Dict[str, Any]]
    ) -> List[SecurityThreat]:
        """Analyze events, emit callbacks, and return detected threats."""
        if not events:
            return []

        features = await self._extract_security_features(events)
        predictions = await self._run_threat_detection_model(features)

        threats: List[SecurityThreat] = []
        for result in predictions:
            level_str = str(result.get("level", "low"))
            try:
                level = ThreatLevel(level_str)
            except ValueError:
                level = ThreatLevel.LOW

            threat = SecurityThreat(
                threat_type=result.get("type", "unknown"),
                level=level,
                score=float(result.get("score", 0.0)),
                metadata=result.get("metadata", {}),
                timestamp=datetime.now(),
            )
            threats.append(threat)

            # log through SecurityAuditor
            try:
                security_auditor.log_security_event(
                    "ml_threat_detected",
                    SecurityLevel[level.name],
                    {"type": threat.threat_type, "score": threat.score},
                )
            except Exception:
                self.logger.exception("Failed to log security event")

            # emit unified callback
            emit_security_event(
                SecurityEvent.THREAT_DETECTED,
                {"type": threat.threat_type, "level": threat.level.value},
            )

        return threats


__all__ = ["SecurityThreat", "ThreatLevel", "MLSecurityEngine"]
