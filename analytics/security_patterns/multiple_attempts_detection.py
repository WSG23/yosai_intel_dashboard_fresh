from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import List, Optional

import pandas as pd

from .types import ThreatIndicator
from .pattern_detection import _attack_info

__all__ = ["detect_multiple_attempts"]


def detect_multiple_attempts(
    df: pd.DataFrame, logger: Optional[logging.Logger] = None
) -> List[ThreatIndicator]:
    """Detect excessive access attempts within short windows."""
    logger = logger or logging.getLogger(__name__)
    threats: List[ThreatIndicator] = []
    try:
        if len(df) == 0:
            return threats
        df_sorted = df.sort_values("timestamp")
        window = timedelta(minutes=5)
        for (person_id, door_id), group in df_sorted.groupby(["person_id", "door_id"]):
            times = group["timestamp"]
            start_idx = 0
            for i in range(len(times)):
                while times[i] - times[start_idx] > window:
                    start_idx += 1
                if i - start_idx + 1 >= 4:
                    threats.append(
                        ThreatIndicator(
                            threat_type="multiple_attempts_anomaly",
                            severity="high",
                            confidence=0.8,
                            description=f"Multiple attempts by {person_id} at door {door_id}",
                            evidence={"user_id": str(person_id), "door_id": str(door_id)},
                            timestamp=datetime.now(),
                            affected_entities=[str(person_id), str(door_id)],
                            attack=_attack_info("multiple_attempts_anomaly"),
                        )
                    )
                    break
    except Exception as exc:  # pragma: no cover - log and continue
        logger.warning("Multiple attempts detection failed: %s", exc)
    return threats
