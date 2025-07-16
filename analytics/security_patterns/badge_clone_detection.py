from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional

import pandas as pd

from .types import ThreatIndicator
from .pattern_detection import _attack_info
from models.enums import AnomalyType

__all__ = ["detect_badge_clone"]


def detect_badge_clone(
    df: pd.DataFrame, logger: Optional[logging.Logger] = None
) -> List[ThreatIndicator]:
    """Detect potential badge cloning based on impossible travel times."""
    logger = logger or logging.getLogger(__name__)
    threats: List[ThreatIndicator] = []
    try:
        if len(df) == 0:
            return threats
        df_sorted = df.sort_values("timestamp")
        for person_id, group in df_sorted.groupby("person_id"):
            prev_door = None
            prev_time = None
            for _, row in group.iterrows():
                if prev_door is not None and row["door_id"] != prev_door:
                    diff = (row["timestamp"] - prev_time).total_seconds()
                    if diff < 60:
                        threats.append(
                            ThreatIndicator(
                                threat_type=AnomalyType.BADGE_CLONE_SUSPECTED,
                                severity="high",
                                confidence=0.8,
                                description=(
                                    f"Badge for {person_id} used at multiple doors within 1 minute"
                                ),
                                evidence={
                                    "person_id": str(person_id),
                                    "first_door": prev_door,
                                    "second_door": row["door_id"],
                                    "time_diff_sec": diff,
                                },
                                timestamp=datetime.now(),
                                affected_entities=[str(person_id)],
                                attack=_attack_info(
                                    AnomalyType.BADGE_CLONE_SUSPECTED.value
                                ),
                            )
                        )
                        break
                prev_door = row["door_id"]
                prev_time = row["timestamp"]
    except Exception as exc:  # pragma: no cover - log and continue
        logger.warning("Badge clone detection failed: %s", exc)
    return threats
