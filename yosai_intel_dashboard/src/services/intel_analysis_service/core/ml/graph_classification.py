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
    graphs to be read from and written to a Neo4j database.  Embeddings produced
    during training are persisted back to Neo4j so that other components or
    subsequent workflows can reuse them.
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
        """Retrieve the current graph from Neo4j.

        Raises
        ------
        ValueError
            If the classifier was initialised without a ``Neo4jClient``.
        """
        if self.neo4j_client is None:
            raise ValueError("Neo4j client not configured")
        return self.neo4j_client.get_graph()

    def write_graph_to_neo4j(self, graph: nx.Graph) -> None:
        """Persist ``graph`` to Neo4j using the configured client.

        Nodes and edges along with their attributes are written via the
        :class:`Neo4jClient`.  When no client is configured a ``ValueError`` is
        raised.  The helper is primarily intended for tests and simple
        end-to-end demos where graphs are manipulated in-memory before being
        pushed to Neo4j.
        """

        if self.neo4j_client is None:
            raise ValueError("Neo4j client not configured")

        for node, data in graph.nodes(data=True):
            self.neo4j_client.add_node(str(node), **data)
        for src, dst, data in graph.edges(data=True):
            rel_type = data.get("type", "RELATED")
            attrs = {k: v for k, v in data.items() if k != "type"}
            self.neo4j_client.add_edge(str(src), str(dst), rel_type, **attrs)

    def _graph_embedding(self, graph: nx.Graph) -> np.ndarray:
        """Return an embedding for ``graph`` and persist it if possible."""
        self.embedder.fit(graph)
        embeddings = self.embedder.get_embeddings()
        if self.neo4j_client is not None:
            self.neo4j_client.write_node_embeddings(embeddings)
            stored = {
                k: np.asarray(v, dtype=float)
                for k, v in self.neo4j_client.read_node_embeddings().items()
            }
            if stored:
                embeddings = stored
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
