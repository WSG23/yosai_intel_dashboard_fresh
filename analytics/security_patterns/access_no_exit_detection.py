from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import List, Optional

import pandas as pd

from .types import ThreatIndicator
from .pattern_detection import _attack_info
from .column_validation import ensure_columns


__all__ = ["detect_access_no_exit"]


def detect_access_no_exit(
    df: pd.DataFrame, logger: Optional[logging.Logger] = None
) -> List[ThreatIndicator]:
    """Detect users who enter but do not exit within a reasonable time."""
    logger = logger or logging.getLogger(__name__)
    threats: List[ThreatIndicator] = []
    try:
        if len(df) == 0:
            return threats
        if not ensure_columns(
            df,
            ["timestamp", "person_id", "door_id", "access_granted"],
            logger,
        ):
            return threats
        df_sorted = df.sort_values("timestamp")
        for person_id, group in df_sorted.groupby("person_id"):
            events = group.reset_index(drop=True)
            for i, row in events.iterrows():
                if row["access_granted"] == 1:
                    subsequent = events[events["timestamp"] > row["timestamp"]]
                    if subsequent.empty or (
                        subsequent.iloc[0]["timestamp"] - row["timestamp"] > timedelta(hours=12)
                    ):
                        threats.append(
                            ThreatIndicator(
                                threat_type=AnomalyType.ACCESS_NO_EXIT,
                                severity="medium",
                                confidence=0.7,
                                description=f"User {person_id} access without exit",
                                evidence={"user_id": str(person_id), "door_id": str(row["door_id"])},
                                timestamp=datetime.now(),
                                affected_entities=[str(person_id)],
                                attack=_attack_info(
                                    AnomalyType.ACCESS_NO_EXIT.value
                                ),
                            )
                        )
    except Exception as exc:  # pragma: no cover - log and continue
        logger.warning("Access-no-exit detection failed: %s", exc)
    return threats
