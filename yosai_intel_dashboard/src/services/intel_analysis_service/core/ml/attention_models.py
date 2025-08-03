"""Attention based models for graphs."""
from __future__ import annotations

from typing import Dict, Mapping

import networkx as nx
import numpy as np


class GraphAttentionNetwork:
    """Simplistic Graph Attention Network.

    The implementation provides a single attention layer that computes new node
    embeddings as an attention-weighted combination of a node and its
    neighbours.  It uses ``numpy`` operations exclusively which keeps the
    dependency footprint small.
    """

    def __init__(self, out_dim: int = 64, alpha: float = 0.2) -> None:
        self.out_dim = out_dim
        self.alpha = alpha
        self.W: np.ndarray | None = None
        self._embeddings: Dict[str, np.ndarray] = {}

    @staticmethod
    def _leaky_relu(x: np.ndarray, alpha: float) -> np.ndarray:
        return np.where(x > 0, x, alpha * x)

    def fit(self, graph: nx.Graph, features: Mapping[str, np.ndarray]) -> "GraphAttentionNetwork":
        nodes = list(graph.nodes())
        in_dim = next(iter(features.values())).shape[0]
        self.W = np.random.randn(in_dim, self.out_dim)
        h = {str(n): features[str(n)] @ self.W for n in nodes}

        for node in nodes:
            node_key = str(node)
            neigh = list(graph.neighbors(node)) + [node]
            z = np.stack([h[str(n)] for n in neigh])
            a = np.random.randn(self.out_dim)
            e = self._leaky_relu(z @ a, self.alpha)
            attn = np.exp(e) / np.sum(np.exp(e))
            self._embeddings[node_key] = attn @ z
        return self

    def get_embeddings(self) -> Mapping[str, np.ndarray]:
        return self._embeddings
