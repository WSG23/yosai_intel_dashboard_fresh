"""Graph anomaly detection algorithms."""

from __future__ import annotations

from collections import Counter
from statistics import mean, stdev
from typing import Any, Dict, List

import networkx as nx
import numpy as np
from sklearn.neighbors import LocalOutlierFactor


def graph_lof(graph: nx.Graph, n_neighbors: int = 20) -> Dict[Any, float]:
    """Compute Local Outlier Factor scores based on simple node features."""
    nodes = list(graph.nodes)
    degrees = np.array([graph.degree(n) for n in nodes], dtype=float)
    clustering = np.array([nx.clustering(graph, n) for n in nodes], dtype=float)
    X = np.vstack([degrees, clustering]).T
    n_neighbors = min(n_neighbors, len(nodes) - 1) if len(nodes) > 1 else 1
    lof = LocalOutlierFactor(n_neighbors=n_neighbors)
    lof.fit(X)
    scores = -lof.negative_outlier_factor_
    return dict(zip(nodes, scores))


def subgraph_pattern_matching(graph: nx.Graph, pattern: nx.Graph) -> List[Dict]:
    """Find subgraphs in *graph* that match *pattern*."""
    matcher = nx.algorithms.isomorphism.GraphMatcher(graph, pattern)
    return [mapping for mapping in matcher.subgraph_isomorphisms_iter()]


def temporal_anomaly_detection(
    graph: nx.Graph,
    time_attr: str = "timestamp",
    bucket=lambda ts: ts,
    threshold: float = 2.0,
) -> List[Any]:
    """Detect time buckets with anomalous edge counts."""
    counts: Counter = Counter()
    for _, _, data in graph.edges(data=True):
        ts = data.get(time_attr)
        if ts is None:
            continue
        counts[bucket(ts)] += 1
    if not counts:
        return []
    values = list(counts.values())
    mu = mean(values)
    sigma = stdev(values) if len(values) > 1 else 0.0
    if sigma == 0.0:
        return []
    return [t for t, c in counts.items() if abs(c - mu) > threshold * sigma]
