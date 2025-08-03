"""High-level API wrappers for graph analytics algorithms."""

from __future__ import annotations

from typing import Any, Dict, List

import networkx as nx

from ..core.algorithms import (
    anomaly_detection,
    centrality,
    community,
    path_analysis,
)


# Community -----------------------------------------------------------------

def detect_communities(graph: nx.Graph, method: str = "louvain", **kwargs) -> List[set]:
    """Expose community detection algorithms.

    Parameters
    ----------
    graph: nx.Graph
        Graph to analyze.
    method: str
        One of ``"louvain"``, ``"label_propagation"`` or ``"hierarchical"``.
    """
    if method == "louvain":
        return community.louvain_communities(graph, **kwargs)
    if method == "label_propagation":
        return community.label_propagation_communities(graph, **kwargs)
    if method == "hierarchical":
        return community.hierarchical_communities(graph, **kwargs)
    raise ValueError(f"Unknown community detection method: {method}")


# Centrality ----------------------------------------------------------------

def compute_centrality(graph: nx.Graph, method: str, **kwargs) -> Dict[Any, float]:
    """Expose centrality measures.

    method may be ``"betweenness"``, ``"pagerank"`` or ``"eigenvector"``.
    """
    if method == "betweenness":
        return centrality.betweenness_centrality(graph, **kwargs)
    if method == "pagerank":
        return centrality.pagerank(graph, **kwargs)
    if method == "eigenvector":
        return centrality.eigenvector_centrality(graph, **kwargs)
    raise ValueError(f"Unknown centrality method: {method}")


# Paths ---------------------------------------------------------------------

def analyze_paths(graph: nx.Graph, analysis: str, **kwargs) -> Any:
    """Perform path-based analysis.

    ``analysis`` can be ``"shortest_path"``, ``"k_hop"`` or ``"temporal"``.
    """
    if analysis == "shortest_path":
        return path_analysis.shortest_path(graph, **kwargs)
    if analysis == "k_hop":
        return path_analysis.k_hop_paths(graph, **kwargs)
    if analysis == "temporal":
        return path_analysis.temporal_path_exists(graph, **kwargs)
    raise ValueError(f"Unknown path analysis type: {analysis}")


# Anomalies -----------------------------------------------------------------

def detect_anomalies(graph: nx.Graph, method: str, **kwargs) -> Any:
    """Detect anomalies in graphs.

    ``method`` can be ``"lof"``, ``"subgraph"`` or ``"temporal"``.
    """
    if method == "lof":
        return anomaly_detection.graph_lof(graph, **kwargs)
    if method == "subgraph":
        return anomaly_detection.subgraph_pattern_matching(graph, **kwargs)
    if method == "temporal":
        return anomaly_detection.temporal_anomaly_detection(graph, **kwargs)
    raise ValueError(f"Unknown anomaly detection method: {method}")
