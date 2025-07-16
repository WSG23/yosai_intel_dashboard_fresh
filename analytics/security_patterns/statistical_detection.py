from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional

import numpy as np
import pandas as pd
from scipy import stats

from .types import ThreatIndicator
from .pattern_detection import _attack_info
from .column_validation import ensure_columns

__all__ = [
    "detect_failure_rate_anomalies",
    "detect_frequency_anomalies",
    "detect_statistical_threats",
]


def detect_failure_rate_anomalies(
    df: pd.DataFrame, logger: Optional[logging.Logger] = None
) -> List[ThreatIndicator]:
    """Detect unusual failure rate patterns."""
    logger = logger or logging.getLogger(__name__)
    threats: List[ThreatIndicator] = []
    try:
        if not ensure_columns(df, ["person_id", "access_granted"], logger):
            return threats
        overall_failure_rate = 1 - df["access_granted"].mean()
        user_failure_rates = df.groupby("person_id")["access_granted"].agg(
            ["mean", "count"]
        )
        user_failure_rates["failure_rate"] = 1 - user_failure_rates["mean"]
        Q1 = user_failure_rates["failure_rate"].quantile(0.25)
        Q3 = user_failure_rates["failure_rate"].quantile(0.75)
        iqr = Q3 - Q1
        outlier_threshold = Q3 + 1.5 * iqr
        high_failure_users = user_failure_rates[
            (user_failure_rates["failure_rate"] > outlier_threshold)
            & (user_failure_rates["count"] >= 5)
        ]
        for user_id, data in high_failure_users.iterrows():
            n_attempts = data["count"]
            n_failures = int(n_attempts * data["failure_rate"])
            p_value = stats.binomtest(
                n_failures, n_attempts, overall_failure_rate
            ).pvalue
            if p_value < 0.05:
                confidence = 1 - p_value
                severity = "critical" if data["failure_rate"] > 0.8 else "high"
                threats.append(
                    ThreatIndicator(
                        threat_type="unusual_failure_rate",
                        severity=severity,
                        confidence=confidence,
                        description=f"User {user_id} has unusually high failure rate: {data['failure_rate']:.2%}",
                        evidence={
                            "user_id": str(user_id),
                            "failure_rate": data["failure_rate"],
                            "attempts": n_attempts,
                            "p_value": p_value,
                            "baseline_rate": overall_failure_rate,
                        },
                        timestamp=datetime.now(),
                        affected_entities=[str(user_id)],
                        attack=_attack_info("unusual_failure_rate"),
                    )
                )
    except Exception as exc:  # pragma: no cover - log and continue
        logger.warning("Failure rate anomaly detection failed: %s", exc)
    return threats


def detect_frequency_anomalies(
    df: pd.DataFrame, logger: Optional[logging.Logger] = None
) -> List[ThreatIndicator]:
    """Detect unusual access frequency patterns."""
    logger = logger or logging.getLogger(__name__)
    threats: List[ThreatIndicator] = []
    try:
        if not ensure_columns(df, ["person_id"], logger):
            return threats
        user_access_counts = df.groupby("person_id").size()
        mean_access = user_access_counts.mean()
        std_access = user_access_counts.std()
        if std_access > 0:
            z_scores = (user_access_counts - mean_access) / std_access
            high_freq_users = user_access_counts[z_scores > 3]
            for user_id, access_count in high_freq_users.items():
                z_score_val = float(z_scores.loc[str(user_id)])
                confidence = min(0.99, (z_score_val - 3) / 3)
                threats.append(
                    ThreatIndicator(
                        threat_type="excessive_access_frequency",
                        severity="medium",
                        confidence=confidence,
                        description=f"User {user_id} has excessive access frequency: {access_count} events",
                        evidence={
                            "user_id": str(user_id),
                            "access_count": access_count,
                            "z_score": z_score_val,
                            "baseline_mean": mean_access,
                        },
                        timestamp=datetime.now(),
                        affected_entities=[str(user_id)],
                        attack=_attack_info("excessive_access_frequency"),
                    )
                )
    except Exception as exc:  # pragma: no cover - log and continue
        logger.warning("Frequency anomaly detection failed: %s", exc)
    return threats


def detect_statistical_threats(
    df: pd.DataFrame, logger: Optional[logging.Logger] = None
) -> List[ThreatIndicator]:
    """Aggregate statistical threat detectors."""
    threats = []
    threats.extend(detect_failure_rate_anomalies(df, logger))
    threats.extend(detect_frequency_anomalies(df, logger))
    return threats
