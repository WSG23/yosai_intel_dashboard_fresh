from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional, Tuple

import pandas as pd

from .types import ThreatIndicator
from .pattern_detection import _attack_info

__all__ = ["detect_odd_path"]


def _extract_paths(df: pd.DataFrame) -> List[Tuple[str, str, str]]:
    df_sorted = df.sort_values("timestamp")
    paths = []
    for person_id, group in df_sorted.groupby("person_id"):
        prev_door = None
        for door in group["door_id"]:
            if prev_door is not None:
                paths.append((person_id, prev_door, door))
            prev_door = door
    return paths


def detect_odd_path(
    df: pd.DataFrame, logger: Optional[logging.Logger] = None
) -> List[ThreatIndicator]:
    """Detect unusual door transition paths for a user."""
    logger = logger or logging.getLogger(__name__)
    threats: List[ThreatIndicator] = []
    try:
        paths = _extract_paths(df)
        if not paths:
            return threats
        path_df = pd.DataFrame(paths, columns=["person_id", "prev", "next"])
        counts = path_df.groupby(["person_id", "prev", "next"]).size()
        rare_paths = counts[counts == 1]
        for (pid, prev, nxt), _ in rare_paths.items():
            threats.append(
                ThreatIndicator(
                    threat_type="odd_path_anomaly",
                    severity="low",
                    confidence=0.6,
                    description=f"User {pid} rare path {prev}->{nxt}",
                    evidence={"user_id": str(pid), "path": f"{prev}->{nxt}"},
                    timestamp=datetime.now(),
                    affected_entities=[str(pid)],
                    attack=_attack_info("odd_path_anomaly"),
                )
            )
    except Exception as exc:  # pragma: no cover - log and continue
        logger.warning("Odd path detection failed: %s", exc)
    return threats
