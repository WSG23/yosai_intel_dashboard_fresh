from __future__ import annotations

from typing import Any, Dict

import pandas as pd

from .base import MappingModel


class HeuristicMappingModel(MappingModel):
    """Simple heuristic-based mapping model."""

    registry_name = "heuristic"

    def suggest(self, df: pd.DataFrame, filename: str) -> Dict[str, Dict[str, Any]]:
        suggestions: Dict[str, Dict[str, Any]] = {}
        for column in df.columns:
            column_lower = str(column).lower()
            field = ""
            confidence = 0.0
            if any(k in column_lower for k in ["person", "user", "employee", "name"]):
                field, confidence = "person_id", 0.7
            elif any(k in column_lower for k in ["door", "location", "device", "room"]):
                field, confidence = "door_id", 0.7
            elif any(k in column_lower for k in ["time", "date", "stamp"]):
                field, confidence = "timestamp", 0.8
            elif any(k in column_lower for k in ["result", "status", "access"]):
                field, confidence = "access_result", 0.7
            elif any(k in column_lower for k in ["token", "badge", "card"]):
                field, confidence = "token_id", 0.6
            suggestions[column] = {"field": field, "confidence": confidence}
        return suggestions
