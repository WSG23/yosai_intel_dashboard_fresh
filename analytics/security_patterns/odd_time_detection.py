from __future__ import annotations

from typing import Dict, List

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

    db = BaselineMetricsDB()
    baselines = {pid: db.get_baseline(pid) or {} for pid in df["person_id"].unique()}
    if not baselines:
        return []

    baseline_df = pd.DataFrame.from_dict(baselines, orient="index")
    baseline_df["person_id"] = baseline_df.index

    frame = df.merge(baseline_df, on="person_id", how="left")
    frame = frame.dropna(subset=["mean_hour"])
    if frame.empty:
        return []

    frame["std_hour"] = frame["std_hour"].fillna(0)

    no_std_mask = frame["std_hour"] == 0
    mismatched = frame[no_std_mask & (frame["hour"] != frame["mean_hour"])]
    threats = [
        Threat("odd_time_access", {"person_id": person})
        for person in mismatched["person_id"].unique()
    ]

    varied = frame[~no_std_mask]
    deviations = varied[
        (varied["hour"] - varied["mean_hour"]).abs() > 2 * varied["std_hour"]
    ]
    first_offenders = (
        deviations.sort_index().drop_duplicates("person_id")[["person_id", "hour"]]
    )
    threats.extend(
        Threat("odd_time_access", {"person_id": row.person_id, "hour": int(row.hour)})
        for row in first_offenders.itertuples(index=False)
    )
    return threats


__all__ = ["BaselineMetricsDB", "detect_odd_time"]
