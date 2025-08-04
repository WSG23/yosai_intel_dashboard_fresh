"""Graph classification utilities."""
from __future__ import annotations

from typing import List, Sequence

import networkx as nx
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

from .embeddings import Node2Vec, GraphSAGE, GCN
from graph.neo4j_client import Neo4jClient


class GraphClassifier:
    """Classify graphs based on learned embeddings.

    The classifier can optionally integrate with :class:`Neo4jClient` allowing
    graphs to be read from and embeddings written back to a Neo4j database.
    """

    def __init__(
        self,
        embedder: Node2Vec | GraphSAGE | GCN | None = None,
        neo4j_client: Neo4jClient | None = None,
    ) -> None:
        self.embedder = embedder or Node2Vec()
        self.model = LogisticRegression()
        self.neo4j_client = neo4j_client

    # ------------------------------------------------------------------
    # Data access helpers
    # ------------------------------------------------------------------
    def load_graph_from_neo4j(self) -> nx.Graph:
        if self.neo4j_client is None:
            raise ValueError("Neo4j client not configured")
        return self.neo4j_client.get_graph()

    def _graph_embedding(self, graph: nx.Graph) -> np.ndarray:
        """Return an embedding for ``graph`` and persist it if possible."""
        self.embedder.fit(graph)
        embeddings = self.embedder.get_embeddings()
        if self.neo4j_client is not None:
            self.neo4j_client.write_node_embeddings(embeddings)
            embeddings = {
                k: np.asarray(v, dtype=float)
                for k, v in self.neo4j_client.read_node_embeddings().items()
            }
        return np.mean(list(embeddings.values()), axis=0)

    # ------------------------------------------------------------------
    # Model API
    # ------------------------------------------------------------------
    def fit(self, graphs: Sequence[nx.Graph], labels: Sequence[int]) -> "GraphClassifier":
        X = [self._graph_embedding(g) for g in graphs]
        self.model.fit(X, labels)
        return self

    def fit_from_neo4j(self, labels: Sequence[int]) -> "GraphClassifier":
        graph = self.load_graph_from_neo4j()
        return self.fit([graph], labels)

    def predict(self, graphs: Sequence[nx.Graph]) -> List[int]:
        X = [self._graph_embedding(g) for g in graphs]
        return list(self.model.predict(X))

    def predict_from_neo4j(self) -> List[int]:
        graph = self.load_graph_from_neo4j()
        return self.predict([graph])

    def evaluate(self, graphs: Sequence[nx.Graph], labels: Sequence[int]) -> float:
        preds = self.predict(graphs)
        return accuracy_score(labels, preds)
