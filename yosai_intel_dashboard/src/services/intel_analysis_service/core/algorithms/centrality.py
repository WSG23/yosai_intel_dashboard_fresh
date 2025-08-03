"""Centrality metrics for graph analytics."""

from __future__ import annotations

from typing import Any, Dict

import networkx as nx


def betweenness_centrality(graph: nx.Graph, **kwargs) -> Dict[Any, float]:
    """Compute betweenness centrality for all nodes."""
    return nx.betweenness_centrality(graph, **kwargs)


def pagerank(graph: nx.Graph, **kwargs) -> Dict[Any, float]:
    """Compute PageRank for nodes."""
    return nx.pagerank(graph, **kwargs)


def eigenvector_centrality(graph: nx.Graph, **kwargs) -> Dict[Any, float]:
    """Compute eigenvector centrality."""
    return nx.eigenvector_centrality(graph, **kwargs)
