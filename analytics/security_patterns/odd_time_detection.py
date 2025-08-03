from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd

from .pattern_detection import Threat


class BaselineMetricsDB:
    """Placeholder baseline storage used for testing."""

    def get_baseline(self, person_id: str) -> Dict[str, float]:
        return {}

    def update_baseline(self, person_id: str, stats: Dict[str, float]) -> None:  # pragma: no cover
        pass


def detect_odd_time(df: pd.DataFrame) -> List[Threat]:
    """Detect access events occurring at unusual hours."""
    if df.empty:
        return []

    threats: List[Threat] = []
    db = BaselineMetricsDB()
    for person, group in df.groupby("person_id"):
        baseline = db.get_baseline(person) or {}
        mean_hour = baseline.get("mean_hour")
        std_hour = baseline.get("std_hour", 0)
        if mean_hour is None:
            continue
        hours = group["hour"].to_numpy()
        if std_hour == 0:
            if np.any(hours != mean_hour):
                threats.append(Threat("odd_time_access", {"person_id": person}))
            continue
        deviations = np.abs(hours - mean_hour)
        mask = deviations > 2 * std_hour
        if np.any(mask):
            threats.append(
                Threat(
                    "odd_time_access",
                    {"person_id": person, "hour": int(hours[mask][0])},
                )
            )
    return threats


__all__ = ["BaselineMetricsDB", "detect_odd_time"]
