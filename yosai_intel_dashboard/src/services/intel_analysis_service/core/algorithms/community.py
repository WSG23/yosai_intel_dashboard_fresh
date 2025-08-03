"""Community detection algorithms."""

from __future__ import annotations

from typing import Iterable, Set, List

import networkx as nx


def louvain_communities(graph: nx.Graph, **kwargs) -> List[Set]:
    """Detect communities using the Louvain method."""
    communities = nx.algorithms.community.louvain_communities(graph, **kwargs)
    return [set(c) for c in communities]


def label_propagation_communities(graph: nx.Graph, **kwargs) -> List[Set]:
    """Detect communities using asynchronous label propagation."""
    communities = nx.algorithms.community.asyn_lpa_communities(graph, **kwargs)
    return [set(c) for c in communities]


def hierarchical_communities(graph: nx.Graph, level: int = 1) -> List[Set]:
    """Return communities from the Girvan-Newman hierarchical clustering.

    Parameters
    ----------
    graph: nx.Graph
        Input graph.
    level: int
        Level of hierarchy to extract. Level 1 yields the first split.
    """
    comp = nx.algorithms.community.girvan_newman(graph)
    communities: Iterable
    for _ in range(level):
        communities = next(comp, None)
        if communities is None:
            break
    if communities is None:
        return [set(graph.nodes)]
    return [set(c) for c in communities]
