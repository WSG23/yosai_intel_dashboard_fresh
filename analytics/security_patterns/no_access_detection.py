from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional

import pandas as pd

from yosai_intel_dashboard.src.core.domain.enums import AccessResult, AnomalyType

from .pattern_detection import _attack_info
from .types import ThreatIndicator

__all__ = ["detect_no_access"]


def detect_no_access(
    df: pd.DataFrame, logger: Optional[logging.Logger] = None
) -> List[ThreatIndicator]:
    """Detect events where access was denied."""
    logger = logger or logging.getLogger(__name__)
    threats: List[ThreatIndicator] = []
    try:
        if len(df) == 0:
            return threats
        denied = df[df["access_result"] == AccessResult.DENIED.value]
        for _, row in denied.iterrows():
            threats.append(
                ThreatIndicator(
                    threat_type=AnomalyType.NO_ACCESS.value,
                    severity="medium",
                    confidence=0.6,
                    description=(
                        f"Access denied for user {row['person_id']} at door {row['door_id']}"
                    ),
                    evidence={
                        "user_id": str(row["person_id"]),
                        "door_id": str(row["door_id"]),
                    },
                    timestamp=datetime.now(),
                    affected_entities=[str(row["person_id"]), str(row["door_id"])],
                    attack=_attack_info(AnomalyType.NO_ACCESS.value),
                )
            )
    except Exception as exc:  # pragma: no cover - log and continue
        logger.warning("No access detection failed: %s", exc)
    return threats
