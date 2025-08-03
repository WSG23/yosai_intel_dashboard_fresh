"""Link prediction utilities."""
from __future__ import annotations

from typing import Mapping, Sequence, Tuple

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score


class LinkPredictor:
    """Predict the likelihood of links between node pairs."""

    def __init__(self) -> None:
        self.model = LogisticRegression()

    @staticmethod
    def _edge_features(embeddings: Mapping[str, np.ndarray], edge: Tuple[str, str]) -> np.ndarray:
        return embeddings[edge[0]] * embeddings[edge[1]]

    def fit(
        self,
        embeddings: Mapping[str, np.ndarray],
        edges: Sequence[Tuple[str, str]],
        labels: Sequence[int],
    ) -> "LinkPredictor":
        X = [self._edge_features(embeddings, (str(u), str(v))) for u, v in edges]
        self.model.fit(X, labels)
        return self

    def predict_proba(
        self, embeddings: Mapping[str, np.ndarray], edge: Tuple[str, str]
    ) -> float:
        feature = self._edge_features(embeddings, (str(edge[0]), str(edge[1])))
        return float(self.model.predict_proba([feature])[0][1])

    def evaluate(
        self,
        embeddings: Mapping[str, np.ndarray],
        edges: Sequence[Tuple[str, str]],
        labels: Sequence[int],
    ) -> float:
        preds = [self.predict_proba(embeddings, e) >= 0.5 for e in edges]
        return accuracy_score(labels, preds)
