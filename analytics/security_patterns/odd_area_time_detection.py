from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional

import pandas as pd

from .types import ThreatIndicator
from .odd_area_detection import _door_to_area
from .pattern_detection import _attack_info

__all__ = ["detect_odd_area_time"]


def detect_odd_area_time(
    df: pd.DataFrame, logger: Optional[logging.Logger] = None
) -> List[ThreatIndicator]:
    """Detect unusual area access specifically occurring after hours."""
    logger = logger or logging.getLogger(__name__)
    threats: List[ThreatIndicator] = []
    try:
        if len(df) == 0:
            return threats
        df = df.copy(deep=False)
        df["area"] = df["door_id"].apply(_door_to_area)
        after_hours = df[df["is_after_hours"] == True]
        for person_id, group in after_hours.groupby("person_id"):
            area_counts = group["area"].value_counts()
            for area, count in area_counts.items():
                if count <= 1:
                    threats.append(
                        ThreatIndicator(
                            threat_type="odd_area_time_anomaly",
                            severity="medium",
                            confidence=0.65,
                            description=f"After-hours access to unusual area {area} by {person_id}",
                            evidence={"user_id": str(person_id), "area": area},
                            timestamp=datetime.now(),
                            affected_entities=[str(person_id)],
                            attack=_attack_info("odd_area_time_anomaly"),
                        )
                    )
    except Exception as exc:  # pragma: no cover - log and continue
        logger.warning("Odd area/time detection failed: %s", exc)
    return threats
