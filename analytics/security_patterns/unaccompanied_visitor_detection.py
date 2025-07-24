from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import List, Optional

import pandas as pd

from .pattern_detection import _attack_info
from .types import ThreatIndicator

__all__ = ["detect_unaccompanied_visitors"]


def detect_unaccompanied_visitors(
    df: pd.DataFrame,
    logger: Optional[logging.Logger] = None,
    *,
    window: timedelta = timedelta(minutes=5),
) -> List[ThreatIndicator]:
    """Detect visitors entering without an accompanying employee."""
    logger = logger or logging.getLogger(__name__)
    threats: List[ThreatIndicator] = []
    try:
        if len(df) == 0:
            return threats
        if not ensure_columns(
            df,
            ["timestamp", "person_id", "door_id", "badge_status"],
            logger,
        ):
            return threats
        df_sorted = df.sort_values("timestamp")
        visitors = df_sorted[df_sorted["badge_status"].str.lower() == "visitor"]
        for _, row in visitors.iterrows():
            window_start = row["timestamp"] - window
            window_end = row["timestamp"] + window
            nearby = df_sorted[
                (df_sorted["timestamp"] >= window_start)
                & (df_sorted["timestamp"] <= window_end)
                & (df_sorted["badge_status"].str.lower() != "visitor")
            ]
            if nearby.empty:
                threats.append(
                    ThreatIndicator(
                        threat_type=AnomalyType.UNACCOMPANIED_VISITOR,
                        severity="medium",
                        confidence=0.7,
                        description=f"Visitor badge {row['person_id']} unaccompanied",
                        evidence={
                            "person_id": str(row["person_id"]),
                            "door_id": str(row["door_id"]),
                        },
                        timestamp=datetime.now(),
                        affected_entities=[str(row["person_id"])],
                        attack=_attack_info(
                            AnomalyType.UNACCOMPANIED_VISITOR.value
                        ),
                    )
                )
    except Exception as exc:  # pragma: no cover - log and continue
        logger.warning("Unaccompanied visitor detection failed: %s", exc)
    return threats
