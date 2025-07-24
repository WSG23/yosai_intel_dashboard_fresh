from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Protocol

import pandas as pd


def _simple_suggestions(columns: list[str]) -> Dict[str, Dict[str, Any]]:
    suggestions: Dict[str, Dict[str, Any]] = {}
    for column in columns:
        c = column.lower()
        suggestion = {"field": "", "confidence": 0.0}
        if any(k in c for k in ["person", "user", "employee", "name"]):
            suggestion = {"field": "person_id", "confidence": 0.7}
        elif any(k in c for k in ["door", "location", "device", "room"]):
            suggestion = {"field": "door_id", "confidence": 0.7}
        elif any(k in c for k in ["time", "date", "stamp"]):
            suggestion = {"field": "timestamp", "confidence": 0.8}
        elif any(k in c for k in ["result", "status", "access"]):
            suggestion = {"field": "access_result", "confidence": 0.7}
        elif any(k in c for k in ["token", "badge", "card"]):
            suggestion = {"field": "token_id", "confidence": 0.6}
        suggestions[column] = suggestion
    return suggestions


class MappingModel(Protocol):
    """Minimal interface for column mapping models."""

    def suggest(self, df: pd.DataFrame, filename: str) -> Dict[str, Dict[str, Any]]:
        ...


class HeuristicMappingModel:
    """Fallback model using simple heuristics."""

    def suggest(self, df: pd.DataFrame, filename: str) -> Dict[str, Dict[str, Any]]:
        return _simple_suggestions(list(df.columns))


class MLMappingModel:
    """Model backed by a :class:`ColumnClassifier`."""

    def __init__(self, model_path: str, vectorizer_path: str) -> None:
        from plugins.ai_classification.database.ai_models import ColumnClassifier

        self.classifier = ColumnClassifier(model_path, vectorizer_path)

    def suggest(self, df: pd.DataFrame, filename: str) -> Dict[str, Dict[str, Any]]:
        headers = list(df.columns)
        if not self.classifier.is_ready():
            return _simple_suggestions(headers)
        preds = self.classifier.predict(headers)
        return {
            h: {"field": field, "confidence": score}
            for h, (field, score) in zip(headers, preds)
        }


def load_model_from_config(path: str) -> MappingModel:
    """Load an ML mapping model from a JSON config file."""
    cfg = json.loads(Path(path).read_text())
    model_path = cfg.get("model_path", "data/column_model.joblib")
    vectorizer_path = cfg.get("vectorizer_path", "data/column_vectorizer.joblib")
    return MLMappingModel(model_path, vectorizer_path)


__all__ = [
    "MappingModel",
    "HeuristicMappingModel",
    "MLMappingModel",
    "load_model_from_config",
]

