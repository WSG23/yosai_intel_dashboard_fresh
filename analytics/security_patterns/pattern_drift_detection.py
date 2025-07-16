from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional

import numpy as np
import pandas as pd
from database.baseline_metrics import BaselineMetricsDB

from .types import ThreatIndicator
from .pattern_detection import _attack_info
from .column_validation import ensure_columns


__all__ = ["detect_pattern_drift"]


def detect_pattern_drift(
    df: pd.DataFrame, logger: Optional[logging.Logger] = None
) -> List[ThreatIndicator]:
    """Detect drift from stored behavioral baselines."""
    logger = logger or logging.getLogger(__name__)
    threats: List[ThreatIndicator] = []
    baseline = BaselineMetricsDB()
    try:
        if len(df) == 0:
            return threats
        if not ensure_columns(df, ["is_after_hours", "access_granted"], logger):
            return threats
        overall_after_hours = float(df["is_after_hours"].mean())
        overall_failure_rate = float(1 - df["access_granted"].mean())
        metrics = baseline.get_baseline("global", "overall")
        base_after_hours = metrics.get("after_hours_rate", overall_after_hours)
        base_failure = metrics.get("failure_rate", overall_failure_rate)
        drift_score = np.sqrt((overall_after_hours - base_after_hours) ** 2 + (overall_failure_rate - base_failure) ** 2)
        if drift_score > 0.2:
            threats.append(
                ThreatIndicator(
                    threat_type=AnomalyType.PATTERN_DRIFT,
                    severity="medium",
                    confidence=min(0.99, drift_score * 2),
                    description="Significant drift in overall access patterns",
                    evidence={
                        "after_hours_rate": overall_after_hours,
                        "failure_rate": overall_failure_rate,
                        "baseline_after_hours": base_after_hours,
                        "baseline_failure_rate": base_failure,
                    },
                    timestamp=datetime.now(),
                    affected_entities=[],
                    attack=_attack_info(AnomalyType.PATTERN_DRIFT.value),
                )
            )
        baseline.update_baseline(
            "global",
            "overall",
            {
                "after_hours_rate": overall_after_hours,
                "failure_rate": overall_failure_rate,
            },
        )
    except Exception as exc:  # pragma: no cover - log and continue
        logger.warning("Pattern drift detection failed: %s", exc)
    return threats
