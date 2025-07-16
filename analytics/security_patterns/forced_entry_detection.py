from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional

import pandas as pd

from .types import ThreatIndicator
from .pattern_detection import _attack_info
from .column_validation import ensure_columns

__all__ = ["detect_forced_entry"]


def detect_forced_entry(
    df: pd.DataFrame, logger: Optional[logging.Logger] = None
) -> List[ThreatIndicator]:
    """Detect potential forced entry or door held open events."""
    logger = logger or logging.getLogger(__name__)
    threats: List[ThreatIndicator] = []
    try:
        if len(df) == 0:
            return threats
        if not ensure_columns(df, ["door_held_open_time", "door_id"], logger):
            return threats
        suspicious = df[df["door_held_open_time"] > 10]
        for _, row in suspicious.iterrows():
            threats.append(
                ThreatIndicator(
                    threat_type="forced_entry_or_door_held_open",
                    severity="high",
                    confidence=0.9,
                    description=f"Door held open too long at {row['door_id']}",
                    evidence={
                        "door_id": str(row["door_id"]),
                        "held_open_time": float(row["door_held_open_time"]),
                    },
                    timestamp=datetime.now(),
                    affected_entities=[str(row["door_id"])],
                    attack=_attack_info("forced_entry_or_door_held_open"),
                )
            )
    except Exception as exc:  # pragma: no cover - log and continue
        logger.warning("Forced entry detection failed: %s", exc)
    return threats
