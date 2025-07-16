from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional

import pandas as pd
from database.baseline_metrics import BaselineMetricsDB

from .types import ThreatIndicator
from .pattern_detection import _attack_info
from models.enums import AnomalyType

__all__ = ["detect_odd_time"]


def detect_odd_time(
    df: pd.DataFrame, logger: Optional[logging.Logger] = None
) -> List[ThreatIndicator]:
    """Detect access events occurring at unusual times for the user."""
    logger = logger or logging.getLogger(__name__)
    threats: List[ThreatIndicator] = []
    baseline = BaselineMetricsDB()
    try:
        if len(df) == 0:
            return threats
        for person_id, group in df.groupby("person_id"):
            hours = group["hour"]
            mean_hour = hours.mean()
            std_hour = hours.std() if hours.std() > 0 else 1
            baseline_metrics = baseline.get_baseline("user", str(person_id))
            base_mean = baseline_metrics.get("mean_hour", mean_hour)
            base_std = baseline_metrics.get("std_hour", std_hour)
            for _, row in group.iterrows():
                if abs(row["hour"] - base_mean) > 2 * base_std:
                    confidence = min(0.99, abs(row["hour"] - base_mean) / (base_std + 1e-9))
                    threats.append(
                        ThreatIndicator(
                            threat_type=AnomalyType.ODD_TIME,
                            severity="medium",
                            confidence=float(confidence),
                            description=f"User {person_id} accessed at unusual hour {row['hour']}",
                            evidence={
                                "user_id": str(person_id),
                                "hour": int(row["hour"]),
                                "baseline_mean": base_mean,
                            },
                            timestamp=datetime.now(),
                            affected_entities=[str(person_id)],
                            attack=_attack_info(AnomalyType.ODD_TIME.value),
                        )
                    )
            baseline.update_baseline(
                "user",
                str(person_id),
                {"mean_hour": mean_hour, "std_hour": std_hour},
            )
    except Exception as exc:  # pragma: no cover - log and continue
        logger.warning("Odd time detection failed: %s", exc)
    return threats
