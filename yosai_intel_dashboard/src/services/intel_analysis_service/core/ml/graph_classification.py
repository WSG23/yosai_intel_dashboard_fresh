"""Graph classification utilities."""
from __future__ import annotations

from typing import List, Sequence

import networkx as nx
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

from .embeddings import Node2Vec, GraphSAGE


class GraphClassifier:
    """Classify graphs based on learned embeddings."""

    def __init__(self, embedder: Node2Vec | GraphSAGE | None = None) -> None:
        self.embedder = embedder or Node2Vec()
        self.model = LogisticRegression()

    def _graph_embedding(self, graph: nx.Graph) -> np.ndarray:
        self.embedder.fit(graph)
        embeddings = self.embedder.get_embeddings()
        return np.mean(list(embeddings.values()), axis=0)

    def fit(self, graphs: Sequence[nx.Graph], labels: Sequence[int]) -> "GraphClassifier":
        X = [self._graph_embedding(g) for g in graphs]
        self.model.fit(X, labels)
        return self

    def predict(self, graphs: Sequence[nx.Graph]) -> List[int]:
        X = [self._graph_embedding(g) for g in graphs]
        return list(self.model.predict(X))

    def evaluate(self, graphs: Sequence[nx.Graph], labels: Sequence[int]) -> float:
        preds = self.predict(graphs)
        return accuracy_score(labels, preds)
