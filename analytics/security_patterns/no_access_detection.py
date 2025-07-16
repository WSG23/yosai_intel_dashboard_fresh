import logging
from datetime import datetime
from typing import List, Optional

import pandas as pd

from database.baseline_metrics import BaselineMetricsDB
from .types import ThreatIndicator
from .pattern_detection import _attack_info

__all__ = ["detect_no_access_anomalies"]


def _max_consecutive_failures(series: pd.Series) -> int:
    """Return the longest run of True values in a boolean Series."""
    max_streak = 0
    streak = 0
    for val in series:
        if bool(val):
            streak += 1
            if streak > max_streak:
                max_streak = streak
        else:
            streak = 0
    return max_streak


def detect_no_access_anomalies(
    df: pd.DataFrame,
    baseline_db: BaselineMetricsDB,
    logger: Optional[logging.Logger] = None,
) -> List[ThreatIndicator]:
    """Flag repeated access denied events per user using baseline failure rates."""
    logger = logger or logging.getLogger(__name__)
    threats: List[ThreatIndicator] = []
    try:
        for user_id, group in df.groupby("person_id"):
            sorted_group = group.sort_values("timestamp")
            failures = sorted_group["access_granted"] == 0
            max_streak = _max_consecutive_failures(failures)
            if max_streak < 3:
                continue
            current_rate = float(1 - group["access_granted"].mean())
            baseline = baseline_db.get_baseline("user", str(user_id)).get(
                "failure_rate"
            )
            if baseline is None:
                continue
            if current_rate > baseline * 1.5 and current_rate - baseline > 0.1:
                severity = "high" if max_streak >= 5 else "medium"
                confidence = min(0.99, current_rate - baseline + max_streak / 10)
                threats.append(
                    ThreatIndicator(
                        threat_type="repeated_access_denied",
                        severity=severity,
                        confidence=confidence,
                        description=(
                            f"User {user_id} had {max_streak} consecutive denied attempts; "
                            f"failure rate {current_rate:.2%} vs baseline {baseline:.2%}"
                        ),
                        evidence={
                            "user_id": str(user_id),
                            "consecutive_failures": max_streak,
                            "current_failure_rate": current_rate,
                            "baseline_failure_rate": baseline,
                        },
                        timestamp=datetime.utcnow(),
                        affected_entities=[str(user_id)],
                        attack=_attack_info("repeated_access_denied"),
                    )
                )
    except Exception as exc:  # pragma: no cover - log and continue
        logger.warning("No-access anomaly detection failed: %s", exc)
    return threats
