from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional

import pandas as pd
from utils.sklearn_compat import optional_import

from .types import ThreatIndicator
from .pattern_detection import _attack_info
from .column_validation import ensure_columns


IsolationForest = optional_import("sklearn.ensemble.IsolationForest")

if IsolationForest is None:  # pragma: no cover - fallback

    class IsolationForest:  # type: ignore
        def __init__(self, *args, **kwargs):
            raise ImportError("scikit-learn is required for IsolationForest")

__all__ = ["detect_critical_door_anomalies"]


def detect_critical_door_anomalies(
    df: pd.DataFrame, logger: Optional[logging.Logger] = None
) -> List[ThreatIndicator]:
    """Detect abnormal activity on critical doors using IsolationForest."""
    logger = logger or logging.getLogger(__name__)
    threats: List[ThreatIndicator] = []
    try:
        if len(df) == 0:
            return threats
        if not ensure_columns(
            df,
            ["timestamp", "person_id", "door_id", "is_after_hours", "access_granted"],
            logger,
        ):
            return threats

        door_stats = df.groupby("door_id").agg(
            after_hours_rate=("is_after_hours", "mean"),
            failure_rate=("access_granted", lambda x: 1 - x.mean()),
        )
        features = door_stats[["after_hours_rate", "failure_rate"]]
        if len(features) < 3:
            return threats
        iso = IsolationForest(contamination=0.1, random_state=42)
        preds = iso.fit_predict(features)
        anomaly_doors = door_stats.index[preds == -1]
        for door_id in anomaly_doors:
            stats = door_stats.loc[door_id]
            confidence = float(
                min(0.99, abs(stats["after_hours_rate"] - features["after_hours_rate"].mean()))
            )
            threats.append(
                ThreatIndicator(
                    threat_type=AnomalyType.CRITICAL_DOOR,
                    severity="high",
                    confidence=confidence,
                    description=f"Door {door_id} shows abnormal usage patterns",
                    evidence={
                        "door_id": str(door_id),
                        "after_hours_rate": stats["after_hours_rate"],
                        "failure_rate": stats["failure_rate"],
                    },
                    timestamp=datetime.now(),
                    affected_entities=[str(door_id)],
                    attack=_attack_info(AnomalyType.CRITICAL_DOOR.value),
                )
            )
    except Exception as exc:  # pragma: no cover - log and continue
        logger.warning("Critical door detection failed: %s", exc)
    return threats
