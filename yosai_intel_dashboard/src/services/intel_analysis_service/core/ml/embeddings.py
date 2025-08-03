"""Embedding algorithms for graph data."""
from __future__ import annotations

from typing import Dict, Iterable, List, Mapping

import networkx as nx
import numpy as np
from gensim.models import Word2Vec


class Node2Vec:
    """Minimal Node2Vec implementation using :mod:`gensim`.

    The implementation is intentionally lightweight and is designed for small
    graphs used in unit tests or interactive experimentation.  It performs
    uniform random walks and trains a ``Word2Vec`` model on the generated
    walks.
    """

    def __init__(
        self,
        dimensions: int = 64,
        walk_length: int = 30,
        num_walks: int = 200,
        workers: int = 1,
    ) -> None:
        self.dimensions = dimensions
        self.walk_length = walk_length
        self.num_walks = num_walks
        self.workers = workers
        self.model: Word2Vec | None = None
        self._embeddings: Dict[str, np.ndarray] = {}

    def _node2vec_walk(self, graph: nx.Graph, start: str) -> List[str]:
        walk = [start]
        for _ in range(self.walk_length - 1):
            cur = walk[-1]
            neighbors = list(graph.neighbors(cur))
            if not neighbors:
                break
            walk.append(str(np.random.choice(neighbors)))
        return walk

    def _generate_walks(self, graph: nx.Graph) -> List[List[str]]:
        nodes: List[str] = [str(n) for n in graph.nodes()]
        walks: List[List[str]] = []
        for _ in range(self.num_walks):
            np.random.shuffle(nodes)
            for node in nodes:
                walks.append(self._node2vec_walk(graph, node))
        return walks

    def fit(self, graph: nx.Graph) -> "Node2Vec":
        walks = self._generate_walks(graph)
        self.model = Word2Vec(
            sentences=walks,
            vector_size=self.dimensions,
            window=10,
            min_count=0,
            sg=1,
            workers=self.workers,
            epochs=1,
        )
        self._embeddings = {str(node): self.model.wv[str(node)] for node in graph.nodes()}
        return self

    def get_embeddings(self) -> Mapping[str, np.ndarray]:
        """Return the learnt node embeddings."""
        return self._embeddings


class GraphSAGE:
    """Very small GraphSAGE style aggregator.

    This implementation averages neighbour features and concatenates them with
    the node's own features.  It is not intended to be a faithful reproduction
    of the original algorithm but provides deterministic embeddings suitable for
    unit tests.
    """

    def __init__(self, dimensions: int = 64, num_layers: int = 2) -> None:
        self.dimensions = dimensions
        self.num_layers = num_layers
        self._embeddings: Dict[str, np.ndarray] = {}

    def fit(
        self, graph: nx.Graph, features: Mapping[str, Iterable[float]] | None = None
    ) -> "GraphSAGE":
        nodes = list(graph.nodes())
        if features is None:
            # Identity features
            features = {str(n): np.eye(len(nodes))[i] for i, n in enumerate(nodes)}
        h: Dict[str, np.ndarray] = {str(n): np.asarray(feat, dtype=float) for n, feat in features.items()}

        for _ in range(self.num_layers):
            new_h: Dict[str, np.ndarray] = {}
            for node in nodes:
                node_key = str(node)
                neighbors = list(graph.neighbors(node))
                neigh_feats = [h[str(n)] for n in neighbors] or [h[node_key]]
                agg = np.mean(neigh_feats, axis=0)
                combined = np.concatenate([h[node_key], agg])
                if combined.shape[0] < self.dimensions:
                    combined = np.pad(combined, (0, self.dimensions - combined.shape[0]))
                else:
                    combined = combined[: self.dimensions]
                new_h[node_key] = combined
            h = new_h
        self._embeddings = h
        return self

    def get_embeddings(self) -> Mapping[str, np.ndarray]:
        """Return node embeddings produced by the last call to :meth:`fit`."""
        return self._embeddings
