from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional

import pandas as pd

from .column_validation import ensure_columns
from .pattern_detection import _attack_info
from .types import ThreatIndicator

__all__ = ["detect_tailgate"]


def detect_tailgate(df: pd.DataFrame, logger: Optional[logging.Logger] = None) -> List[ThreatIndicator]:
    """Detect probable tailgating events based on rapid successive entries."""
    logger = logger or logging.getLogger(__name__)
    threats: List[ThreatIndicator] = []
    try:
        if len(df) == 0:
            return threats
        if not ensure_columns(df, ["timestamp", "person_id", "door_id"], logger):
            return threats
        df_sorted = df.sort_values("timestamp")
        for door_id, group in df_sorted.groupby("door_id"):
            time_diff = group["timestamp"].diff().dt.total_seconds()
            suspicious = group[time_diff.between(1, 5)]
            for _, row in suspicious.iterrows():
                threats.append(
                    ThreatIndicator(
                        threat_type=AnomalyType.PROBABLE_TAILGATE,
                        severity="medium",
                        confidence=0.75,
                        description=f"Possible tailgate at door {door_id}",
                        evidence={
                            "door_id": str(door_id),
                            "timestamp": row["timestamp"],
                        },
                        timestamp=datetime.now(),
                        affected_entities=[str(row["person_id"]), str(door_id)],
                        attack=_attack_info(AnomalyType.PROBABLE_TAILGATE.value),
                    )
                )
    except Exception as exc:  # pragma: no cover - log and continue
        logger.warning("Tailgate detection failed: %s", exc)
    return threats
