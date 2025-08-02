from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import pandas as pd


@dataclass
class Threat:
    """Simple representation of a detected threat."""

    threat_type: str
    details: Dict[str, object]


def detect_critical_door_risks(df: pd.DataFrame) -> List[Threat]:
    """Detect repeated denied attempts on critical doors."""
    if df.empty:
        return []
    crit = df[
        (df.get("door_type") == "critical")
        & (df.get("access_result") == "Denied")
        & (df.get("clearance_level", 0) < df.get("required_clearance", 0))
    ]
    if crit.empty:
        return []
    return [Threat("critical_door_anomaly", {"events": crit.to_dict("records")})]


__all__ = ["Threat", "detect_critical_door_risks"]
