from __future__ import annotations

from typing import Dict, Iterator

import numpy as np
import pandas as pd

from .pattern_detection import Threat


class BaselineMetricsDB:
    """Placeholder baseline storage used for testing."""

    def get_baseline(self, person_id: str) -> Dict[str, float]:
        return {}

    def update_baseline(
        self, person_id: str, stats: Dict[str, float]
    ) -> None:  # pragma: no cover
        pass


def detect_odd_time(df: pd.DataFrame) -> Iterator[Threat]:
    """Detect access events occurring at unusual hours.

    Yields
    ------
    Threat
        An ``odd_time_access`` threat for users accessing outside their
        typical hours.
    """
    if df.empty:
        return

    db = BaselineMetricsDB()
    for person, group in df.groupby("person_id"):
        baseline = db.get_baseline(person) or {}
        mean_hour = baseline.get("mean_hour")
        std_hour = baseline.get("std_hour", 0)
        if mean_hour is None:
            continue
        hours = group["hour"].to_numpy()
        if std_hour == 0:
            if any(h != mean_hour for h in hours):
                yield Threat("odd_time_access", {"person_id": person})
            continue
        for h in hours:
            if abs(h - mean_hour) > 2 * std_hour:
                yield Threat("odd_time_access", {"person_id": person, "hour": int(h)})
                break

__all__ = ["BaselineMetricsDB", "detect_odd_time"]
