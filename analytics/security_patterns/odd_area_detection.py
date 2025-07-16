from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional

import pandas as pd

from .types import ThreatIndicator
from .pattern_detection import _attack_info
from .utils import _door_to_area

__all__ = ["detect_odd_area"]


def detect_odd_area(
    df: pd.DataFrame, logger: Optional[logging.Logger] = None
) -> List[ThreatIndicator]:
    """Detect access to unusual areas for a user based on door prefix."""
    logger = logger or logging.getLogger(__name__)
    threats: List[ThreatIndicator] = []
    try:
        if len(df) == 0:
            return threats
        df = df.copy(deep=False)
        df["area"] = df["door_id"].apply(_door_to_area)
        for person_id, group in df.groupby("person_id"):
            total = len(group)
            area_counts = group["area"].value_counts()
            for area, count in area_counts.items():
                rate = count / total
                if rate < 0.1 and count <= 2:
                    threats.append(
                        ThreatIndicator(
                            threat_type="odd_area_anomaly",
                            severity="low",
                            confidence=0.55,
                            description=f"User {person_id} rarely accesses area {area}",
                            evidence={"user_id": str(person_id), "area": area},
                            timestamp=datetime.now(),
                            affected_entities=[str(person_id)],
                            attack=_attack_info("odd_area_anomaly"),
                        )
                    )
    except Exception as exc:  # pragma: no cover - log and continue
        logger.warning("Odd area detection failed: %s", exc)
    return threats
