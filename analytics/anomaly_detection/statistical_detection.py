from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from utils.scipy_compat import get_stats_module
stats = get_stats_module()

__all__ = [
    "detect_frequency_anomalies",
    "detect_statistical_anomalies",
    "calculate_severity_from_zscore",
]


def detect_frequency_anomalies(df: pd.DataFrame, logger: Optional[logging.Logger] = None) -> List[Dict[str, Any]]:
    """Detect frequency-based anomalies."""
    logger = logger or logging.getLogger(__name__)
    anomalies: List[Dict[str, Any]] = []
    try:
        person_stats = df.groupby('person_id').agg({
            'timestamp': ['count', 'min', 'max'],
            'access_granted': 'sum'
        }).round(2)
        person_stats.columns = ['total_attempts', 'first_access', 'last_access', 'successful_attempts']
        freq_threshold = person_stats['total_attempts'].quantile(0.95)
        high_freq_users = person_stats[person_stats['total_attempts'] > freq_threshold]
        for person_id, stats in high_freq_users.iterrows():
            anomalies.append({
                "type": "activity_burst",
                "user_id": person_id,
                "details": {
                    "total_attempts": int(stats['total_attempts']),
                    "successful_attempts": int(stats['successful_attempts']),
                    "time_span": str(stats['last_access'] - stats['first_access'])
                },
                "severity": "medium",
                "confidence": 0.8,
                "timestamp": datetime.now()
            })
    except Exception as exc:  # pragma: no cover - log and continue
        logger.warning("Frequency anomaly detection failed: %s", exc)
    return anomalies


def calculate_severity_from_zscore(z_score: float) -> str:
    """Calculate severity level from Z-score."""
    if z_score >= 4.0:
        return "critical"
    elif z_score >= 3.5:
        return "high"
    elif z_score >= 3.0:
        return "medium"
    else:
        return "low"


def detect_statistical_anomalies(df: pd.DataFrame, sensitivity: float, logger: Optional[logging.Logger] = None) -> List[Dict[str, Any]]:
    """Detect statistical anomalies using Z-score and IQR methods."""
    logger = logger or logging.getLogger(__name__)
    anomalies: List[Dict[str, Any]] = []
    try:
        hourly_access = df.groupby(df['timestamp'].dt.hour).size()
        z_scores = np.abs(stats.zscore(hourly_access))
        anomalous_hours = hourly_access[z_scores > (3.0 * (1 - sensitivity))]
        for hour, count in anomalous_hours.items():
            anomalies.append({
                "type": "unusual_hour_activity",
                "details": {
                    "hour": int(hour),
                    "access_count": int(count),
                    "z_score": float(z_scores[hour])
                },
                "severity": calculate_severity_from_zscore(z_scores[hour]),
                "confidence": min(0.95, abs(z_scores[hour]) / 4.0),
                "timestamp": datetime.now()
            })
    except Exception as exc:  # pragma: no cover - log and continue
        logger.warning("Statistical anomaly detection failed: %s", exc)
    return anomalies
