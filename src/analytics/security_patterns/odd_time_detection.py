from __future__ import annotations

from typing import Dict, Iterator

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
        return (x for x in [])

    db = BaselineMetricsDB()
    baselines = {pid: db.get_baseline(pid) or {} for pid in df["person_id"].unique()}
    if not baselines:
        return (x for x in [])

    baseline_df = pd.DataFrame.from_dict(baselines, orient="index")
    if baseline_df.empty or "mean_hour" not in baseline_df.columns:
        return (x for x in [])
    baseline_df["person_id"] = baseline_df.index

    frame = df.merge(baseline_df, on="person_id", how="left")
    frame = frame.dropna(subset=["mean_hour"])
    if frame.empty:
        return (x for x in [])

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
    return (t for t in threats)


__all__ = ["BaselineMetricsDB", "detect_odd_time"]
