from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional

import pandas as pd

from .types import ThreatIndicator
from .pattern_detection import _attack_info
from models.enums import AnomalyType
from database.baseline_metrics import BaselineMetricsDB

__all__ = ["detect_odd_door_usage"]


def detect_odd_door_usage(
    df: pd.DataFrame, logger: Optional[logging.Logger] = None
) -> List[ThreatIndicator]:
    """Detect user access to rarely used doors compared to baseline."""
    logger = logger or logging.getLogger(__name__)
    threats: List[ThreatIndicator] = []
    baseline = BaselineMetricsDB()
    try:
        if len(df) == 0:
            return threats
        for person_id, group in df.groupby("person_id"):
            total = len(group)
            door_counts = group["door_id"].value_counts()
            baseline_metrics = baseline.get_baseline("user", str(person_id))
            for door_id, count in door_counts.items():
                metric = f"door_{door_id}_rate"
                rate = count / total
                base_rate = baseline_metrics.get(metric)
                if base_rate is not None and rate > base_rate * 2 and rate - base_rate > 0.05:
                    confidence = min(0.99, rate - base_rate)
                    threats.append(
                        ThreatIndicator(
                            threat_type=AnomalyType.ODD_DOOR,
                            severity="medium",
                            confidence=confidence,
                            description=f"User {person_id} unusual access to door {door_id}",
                            evidence={
                                "user_id": str(person_id),
                                "door_id": str(door_id),
                                "rate": rate,
                                "baseline_rate": base_rate,
                            },
                            timestamp=datetime.now(),
                            affected_entities=[str(person_id), str(door_id)],
                            attack=_attack_info(AnomalyType.ODD_DOOR.value),
                        )
                    )
            # update baseline
            metrics = {f"door_{d}_rate": c / total for d, c in door_counts.items()}
            baseline.update_baseline("user", str(person_id), metrics)
    except Exception as exc:  # pragma: no cover - log and continue
        logger.warning("Odd door detection failed: %s", exc)
    return threats
