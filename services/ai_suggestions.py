"""Simple column suggestion heuristics used across the app."""

from typing import Dict, List, Any


def generate_column_suggestions(columns: List[str]) -> Dict[str, Dict[str, Any]]:
    """Return suggested standard fields for each column name."""
    suggestions: Dict[str, Dict[str, Any]] = {}

    for column in columns:
        column_lower = column.lower()
        suggestion = {"field": "", "confidence": 0.0}

        if any(
            keyword in column_lower
            for keyword in ["person", "user", "employee", "name"]
        ):
            suggestion = {"field": "person_id", "confidence": 0.7}
        elif any(
            keyword in column_lower
            for keyword in ["door", "location", "device", "room"]
        ):
            suggestion = {"field": "door_id", "confidence": 0.7}
        elif any(keyword in column_lower for keyword in ["time", "date", "stamp"]):
            suggestion = {"field": "timestamp", "confidence": 0.8}
        elif any(keyword in column_lower for keyword in ["result", "status", "access"]):
            suggestion = {"field": "access_result", "confidence": 0.7}
        elif any(keyword in column_lower for keyword in ["token", "badge", "card"]):
            suggestion = {"field": "token_id", "confidence": 0.6}

        suggestions[column] = suggestion

    return suggestions


__all__ = ["generate_column_suggestions"]
