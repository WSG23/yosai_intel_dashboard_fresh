from __future__ import annotations

import logging
import warnings
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import yaml

from .types import ThreatIndicator
from utils.sklearn_compat import optional_import

LogisticRegression = optional_import("sklearn.linear_model.LogisticRegression")

if LogisticRegression is None:  # pragma: no cover - fallback

    class LogisticRegression:  # type: ignore
        def __init__(self, *args, **kwargs):
            raise ImportError("scikit-learn is required for LogisticRegression")

__all__ = [
    "detect_pattern_threats",
    "detect_rapid_attempts",
    "detect_after_hours_anomalies",
    "detect_critical_door_risks",
    "_attack_info",
]

# ---------------------------------------------------------------------------
# MITRE ATT&CK mapping
# ---------------------------------------------------------------------------
_mapping_file = (
    Path(__file__).resolve().parents[2] / "resources" / "attack_techniques.yaml"
)
try:
    with _mapping_file.open("r", encoding="utf-8") as fh:
        _ATTACK_MAP: Dict[str, Dict[str, str]] = yaml.safe_load(fh) or {}
except Exception as exc:  # pragma: no cover - environment may not have file
    logging.getLogger(__name__).warning("Failed to load ATT&CK mapping: %s", exc)
    _ATTACK_MAP = {}


def _attack_info(threat_type: str) -> Optional[Dict[str, str]]:
    """Return ATT&CK technique info for a threat type."""
    info = _ATTACK_MAP.get(threat_type)
    return dict(info) if isinstance(info, dict) else None


def detect_rapid_attempts(
    df: pd.DataFrame, logger: Optional[logging.Logger] = None
) -> List[ThreatIndicator]:
    """Detect rapid successive access attempts."""
    logger = logger or logging.getLogger(__name__)
    threats: List[ThreatIndicator] = []
    try:
        df_sorted = df.sort_values(["person_id", "timestamp"])
        df_sorted["time_diff"] = df_sorted.groupby("person_id")["timestamp"].diff()
        rapid_threshold = pd.Timedelta(seconds=30)
        rapid_attempts = df_sorted[df_sorted["time_diff"] < rapid_threshold]
        if len(rapid_attempts) > 0:
            user_rapid_counts = rapid_attempts.groupby("person_id").size()
            for user_id, count in user_rapid_counts.items():
                if count >= 3:
                    user_rapid_data = rapid_attempts[
                        rapid_attempts["person_id"] == user_id
                    ]
                    failure_rate = 1 - user_rapid_data["access_granted"].mean()
                    severity = "critical" if failure_rate > 0.7 else "high"
                    confidence = min(0.95, count / 10)
                    threats.append(
                        ThreatIndicator(
                            threat_type="rapid_access_attempts",
                            severity=severity,
                            confidence=confidence,
                            description=f"User {user_id} made {count} rapid access attempts",
                            evidence={
                                "user_id": str(user_id),
                                "rapid_attempts": count,
                                "failure_rate": failure_rate,
                                "time_window": "within_30_seconds",
                            },
                            timestamp=datetime.now(),
                            affected_entities=[str(user_id)],
                            attack=_attack_info("rapid_access_attempts"),
                        )
                    )
    except Exception as exc:  # pragma: no cover - log and continue
        logger.warning("Rapid attempts detection failed: %s", exc)
    return threats


def detect_after_hours_anomalies(
    df: pd.DataFrame, logger: Optional[logging.Logger] = None
) -> List[ThreatIndicator]:
    """Detect suspicious after-hours access patterns."""
    logger = logger or logging.getLogger(__name__)
    threats: List[ThreatIndicator] = []
    try:
        after_hours_data = df[df["is_after_hours"] == True]
        if len(after_hours_data) == 0:
            return threats
        user_after_hours = after_hours_data.groupby("person_id").size().astype(float)
        threshold = user_after_hours.quantile(0.9)
        excessive_users = user_after_hours[user_after_hours > threshold]
        for user_id, count in excessive_users.items():
            user_total = len(df[df["person_id"] == user_id])
            after_hours_rate = count / user_total
            if after_hours_rate > 0.3:
                threats.append(
                    ThreatIndicator(
                        threat_type="excessive_after_hours_access",
                        severity="medium",
                        confidence=min(0.9, after_hours_rate),
                        description=f"User {user_id} has excessive after-hours access: {count} events ({after_hours_rate:.1%})",
                        evidence={
                            "user_id": str(user_id),
                            "after_hours_count": count,
                            "after_hours_rate": after_hours_rate,
                            "total_events": user_total,
                        },
                        timestamp=datetime.now(),
                        affected_entities=[str(user_id)],
                        attack=_attack_info("excessive_after_hours_access"),
                    )
                )
    except Exception as exc:  # pragma: no cover - log and continue
        logger.warning("After-hours anomaly detection failed: %s", exc)
    return threats


def detect_critical_door_risks(
    df: pd.DataFrame, logger: Optional[logging.Logger] = None
) -> List[ThreatIndicator]:
    """Detect high risk attempts on critical doors."""
    logger = logger or logging.getLogger(__name__)
    threats: List[ThreatIndicator] = []
    try:
        if "door_type" not in df.columns:
            return threats

        critical = df[df["door_type"].astype(str).str.lower() == "critical"]
        if len(critical) == 0:
            return threats

        # Derive simple features for ML model
        features = pd.DataFrame()
        features["after_hours"] = critical.get("is_after_hours", False).astype(int)
        if "required_clearance" in critical.columns and "clearance_level" in critical.columns:
            gap = critical["required_clearance"] - critical["clearance_level"]
            features["clearance_gap"] = gap.clip(lower=0)
        else:
            features["clearance_gap"] = 0

        labels = (critical["access_granted"] == 0).astype(int)

        if labels.nunique() < 2:
            # Fallback heuristic if only one class present
            base_prob = 0.8 if features["after_hours"].iloc[0] else 0.6
            probs = base_prob + 0.1 * features["clearance_gap"].fillna(0)
        else:
            model = LogisticRegression(max_iter=100)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                model.fit(features, labels)

            probs = model.predict_proba(features)[:, 1]
        for idx, prob in enumerate(probs):
            if prob < 0.7:
                continue
            row = critical.iloc[idx]
            severity = "critical" if prob > 0.9 else "high"
            threats.append(
                ThreatIndicator(
                    threat_type="critical_door_anomaly",
                    severity=severity,
                    confidence=float(prob),
                    description=(
                        f"High risk attempt on critical door {row['door_id']} by user"
                        f" {row['person_id']} (risk {prob:.2f})"
                    ),
                    evidence={
                        "user_id": str(row["person_id"]),
                        "door_id": str(row["door_id"]),
                        "risk_score": float(prob),
                        "after_hours": bool(row.get("is_after_hours", False)),
                        "clearance_gap": float(features.loc[row.name, "clearance_gap"]),
                    },
                    timestamp=row["timestamp"],
                    affected_entities=[str(row["person_id"]), str(row["door_id"])],
                    attack=_attack_info("critical_door_activity"),
                )
            )
    except Exception as exc:  # pragma: no cover - log and continue
        logger.warning("Critical door risk detection failed: %s", exc)
    return threats


def detect_pattern_threats(
    df: pd.DataFrame, logger: Optional[logging.Logger] = None
) -> List[ThreatIndicator]:
    """Run all pattern-based threat detectors."""
    threats = []
    threats.extend(detect_rapid_attempts(df, logger))
    threats.extend(detect_after_hours_anomalies(df, logger))
    return threats
