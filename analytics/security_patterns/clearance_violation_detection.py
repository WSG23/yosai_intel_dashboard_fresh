from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional

import pandas as pd

from .types import ThreatIndicator
from .pattern_detection import _attack_info

__all__ = ["detect_clearance_violations"]


def detect_clearance_violations(
    df: pd.DataFrame, logger: Optional[logging.Logger] = None
) -> List[ThreatIndicator]:
    """Detect access where user clearance is below door requirement."""
    logger = logger or logging.getLogger(__name__)
    threats: List[ThreatIndicator] = []
    try:
        if len(df) == 0:
            return threats
        if "user_clearance" not in df.columns or "required_clearance" not in df.columns:
            return threats
        violations = df[df["user_clearance"] < df["required_clearance"]]
        for _, row in violations.iterrows():
            threats.append(
                ThreatIndicator(
                    threat_type="access_outside_clearance_anomaly",
                    severity="high",
                    confidence=0.9,
                    description=f"User {row['person_id']} lacks clearance for door {row['door_id']}",
                    evidence={
                        "user_id": str(row["person_id"]),
                        "door_id": str(row["door_id"]),
                        "user_clearance": row["user_clearance"],
                        "required_clearance": row["required_clearance"],
                    },
                    timestamp=datetime.now(),
                    affected_entities=[str(row["person_id"]), str(row["door_id"])],
                    attack=_attack_info("access_outside_clearance_anomaly"),
                )
            )
    except Exception as exc:  # pragma: no cover - log and continue
        logger.warning("Clearance violation detection failed: %s", exc)
    return threats
