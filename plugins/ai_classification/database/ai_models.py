"""Lightweight models used by the AI classification plugin."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple

import joblib

from utils.sklearn_compat import optional_import

TfidfVectorizer = optional_import("sklearn.feature_extraction.text.TfidfVectorizer")
LogisticRegression = optional_import("sklearn.linear_model.LogisticRegression")

if LogisticRegression is None:  # pragma: no cover - fallback

    class LogisticRegression:  # type: ignore
        def __init__(self, *args, **kwargs):
            raise ImportError("scikit-learn is required for LogisticRegression")


if TfidfVectorizer is None:  # pragma: no cover - fallback

    class TfidfVectorizer:  # type: ignore
        def __init__(self, *args, **kwargs):
            raise ImportError("scikit-learn is required for TfidfVectorizer")


class ColumnClassifier:
    """Wrap a trained scikit-learn model for column type prediction."""

    def __init__(self, model_path: str, vectorizer_path: str) -> None:
        self.model_path = Path(model_path)
        self.vectorizer_path = Path(vectorizer_path)
        self.model: Optional[LogisticRegression] = None
        self.vectorizer: Optional[TfidfVectorizer] = None
        self._load()

    def _load(self) -> None:
        if self.model_path.exists() and self.vectorizer_path.exists():
            self.model = joblib.load(self.model_path)
            self.vectorizer = joblib.load(self.vectorizer_path)

    def is_ready(self) -> bool:
        return self.model is not None and self.vectorizer is not None

    def predict(self, headers: List[str]) -> List[Tuple[str, float]]:
        if not self.is_ready():
            raise RuntimeError("model not loaded")
        X = self.vectorizer.transform(headers)
        probs = self.model.predict_proba(X)
        labels = self.model.classes_
        results: List[Tuple[str, float]] = []
        for p in probs:
            idx = int(p.argmax())
            results.append((str(labels[idx]), float(p[idx])))
        return results
