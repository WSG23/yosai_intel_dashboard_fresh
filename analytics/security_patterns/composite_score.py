from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional

import numpy as np
import pandas as pd
from utils.sklearn_compat import optional_import

from .types import ThreatIndicator
from .pattern_detection import _attack_info
from models.enums import AnomalyType

IsolationForest = optional_import("sklearn.ensemble.IsolationForest")

if IsolationForest is None:  # pragma: no cover

    class IsolationForest:  # type: ignore
        def __init__(self, *args, **kwargs):
            raise ImportError("scikit-learn is required for IsolationForest")

__all__ = ["detect_composite_score"]


def detect_composite_score(
    df: pd.DataFrame, logger: Optional[logging.Logger] = None
) -> List[ThreatIndicator]:
    """Compute composite anomaly scores and flag extreme events."""
    logger = logger or logging.getLogger(__name__)
    threats: List[ThreatIndicator] = []
    try:
        if len(df) < 5:
            return threats
        features = df[["hour", "is_after_hours", "access_granted"]].astype(float)
        iso = IsolationForest(contamination=0.1, random_state=42)
        scores = -iso.fit_predict(features)
        anomaly_indices = np.where(scores > 0)[0]
        for idx in anomaly_indices:
            row = df.iloc[idx]
            threats.append(
                ThreatIndicator(
                    threat_type=AnomalyType.COMPOSITE_SCORE,
                    severity="low",
                    confidence=0.6,
                    description="Composite anomaly detected",
                    evidence={
                        "person_id": str(row["person_id"]),
                        "door_id": str(row["door_id"]),
                    },
                    timestamp=datetime.now(),
                    affected_entities=[str(row["person_id"])],
                    attack=_attack_info(AnomalyType.COMPOSITE_SCORE.value),
                )
            )
    except Exception as exc:  # pragma: no cover - log and continue
        logger.warning("Composite score detection failed: %s", exc)
    return threats
