from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional

import pandas as pd

from .types import ThreatIndicator
from .pattern_detection import _attack_info
from .column_validation import ensure_columns


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
        if not ensure_columns(
            df,
            ["timestamp", "person_id", "door_id", "user_clearance", "required_clearance"],
            logger,
        ):
            return threats
        violations = df[df["user_clearance"] < df["required_clearance"]]
        for _, row in violations.iterrows():
            threats.append(
                ThreatIndicator(
                    threat_type=AnomalyType.ACCESS_OUTSIDE_CLEARANCE,
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
                    attack=_attack_info(
                        AnomalyType.ACCESS_OUTSIDE_CLEARANCE.value
                    ),
                )
            )
    except Exception as exc:  # pragma: no cover - log and continue
        logger.warning("Clearance violation detection failed: %s", exc)
    return threats
