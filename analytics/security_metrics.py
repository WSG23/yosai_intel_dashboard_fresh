"""Security metrics data structure."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Tuple


@dataclass
class SecurityMetrics:
    """Structure representing overall security scoring metrics."""

    score: float
    threat_level: str
    confidence_interval: Tuple[float, float]
    method: str
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        if not 0 <= self.score <= 100:
            raise ValueError("score must be between 0 and 100")

        valid_levels = {"low", "medium", "high", "critical"}
        if self.threat_level not in valid_levels:
            raise ValueError(f"threat_level must be one of {valid_levels}")

        if (
            len(self.confidence_interval) != 2
            or self.confidence_interval[0] > self.confidence_interval[1]
            or not 0 <= self.confidence_interval[0] <= 100
            or not 0 <= self.confidence_interval[1] <= 100
        ):
            raise ValueError(
                "confidence_interval must be two ascending values between 0 and 100"
            )

        if not self.method:
            raise ValueError("method cannot be empty")

        if not isinstance(self.timestamp, datetime):
            raise ValueError("timestamp must be datetime instance")
