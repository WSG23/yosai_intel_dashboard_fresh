"""Library of graph algorithms used by the security dashboard.

The implementations lean on :mod:`networkx` for graph operations and are
sized for clarity rather than raw performance.  Each function accepts either a
:class:`networkx` graph or a :class:`~analytics.graph_analysis.schema.GraphModel`
instance.
"""

from __future__ import annotations

from collections import defaultdict
from itertools import combinations
from statistics import mean, stdev
from typing import Dict, Iterable, List, Sequence, Tuple

import networkx as nx
from sklearn.neighbors import LocalOutlierFactor

from .schema import GraphModel


def _to_nx(graph: GraphModel | nx.Graph) -> nx.Graph:
    """Return an underlying :mod:`networkx` graph."""

    if isinstance(graph, GraphModel):
        return graph.graph
    return graph


# ---------------------------------------------------------------------------
# Community detection
# ---------------------------------------------------------------------------


def louvain_communities(graph: GraphModel | nx.Graph) -> List[set]:
    """Compute communities using the Louvain method."""

    G = _to_nx(graph)
    return list(nx.algorithms.community.louvain_communities(G, weight="weight"))


def label_propagation_communities(graph: GraphModel | nx.Graph) -> List[set]:
    """Detect communities via asynchronous label propagation."""

    G = _to_nx(graph)
    return [
        set(c) for c in nx.algorithms.community.asyn_lpa_communities(G, weight="weight")
    ]


def hierarchical_communities(
    graph: GraphModel | nx.Graph, depth: int = 2
) -> List[Tuple[set, ...]]:
    """Hierarchical clustering using the Girvan–Newman algorithm."""

    G = _to_nx(graph)
    comp = nx.algorithms.community.girvan_newman(G)
    return [tuple(map(set, communities)) for _, communities in zip(range(depth), comp)]


# ---------------------------------------------------------------------------
# Centrality measures
# ---------------------------------------------------------------------------


def betweenness_centrality(graph: GraphModel | nx.Graph) -> Dict:
    """Betweenness centrality for all nodes."""

    G = _to_nx(graph)
    return nx.betweenness_centrality(G)


def pagerank_scores(graph: GraphModel | nx.Graph) -> Dict:
    """PageRank scores for all nodes."""

    G = _to_nx(graph)
    return nx.pagerank(G, weight="weight")


def eigenvector_centrality_scores(graph: GraphModel | nx.Graph) -> Dict:
    """Eigenvector centrality for all nodes."""

    G = _to_nx(graph)
    return nx.eigenvector_centrality(G, weight="weight")


# ---------------------------------------------------------------------------
# Path analysis
# ---------------------------------------------------------------------------


def shortest_path(graph: GraphModel | nx.Graph, source: str, target: str) -> List[str]:
    """Shortest path between two nodes."""

    G = _to_nx(graph)
    return nx.shortest_path(G, source, target, weight="weight")


def all_paths_up_to_length(
    graph: GraphModel | nx.Graph, source: str, target: str, max_len: int
) -> List[List[str]]:
    """Enumerate all simple paths up to ``max_len`` between ``source`` and ``target``."""

    G = _to_nx(graph)
    return list(nx.all_simple_paths(G, source, target, cutoff=max_len))


def temporal_paths(
    graph: GraphModel, source: str, target: str, start: float, end: float
) -> List[List[str]]:
    """Find paths within a temporal window."""

    subgraph = graph.get_subgraph_by_time(start, end)
    return list(nx.all_simple_paths(subgraph, source, target))


# ---------------------------------------------------------------------------
# Anomaly detection and pattern analysis
# ---------------------------------------------------------------------------


def graph_lof(graph: GraphModel | nx.Graph, n_neighbors: int = 5) -> Dict[str, float]:
    """Local Outlier Factor scores based on node degrees."""

    G = _to_nx(graph)
    features = [[d] for _, d in G.degree()]
    if len(features) <= 1:
        return {}
    n_neighbors = max(1, min(n_neighbors, len(features) - 1))
    lof = LocalOutlierFactor(n_neighbors=n_neighbors)
    lof.fit(features)
    return {node: score for node, score in zip(G.nodes(), lof.negative_outlier_factor_)}


def subgraph_pattern_match(
    graph: GraphModel | nx.Graph, pattern: nx.Graph
) -> List[Dict[str, str]]:
    """Return mappings where ``pattern`` matches a subgraph of ``graph``."""

    G = _to_nx(graph)
    matcher = nx.algorithms.isomorphism.DiGraphMatcher(G, pattern)
    return list(matcher.subgraph_isomorphisms_iter())


def temporal_anomaly_detection(
    snapshots: Sequence[Tuple[float, GraphModel]],
) -> List[float]:
    """Detect timestamps with large edge count deltas between snapshots."""

    counts = [(ts, g.graph.number_of_edges()) for ts, g in snapshots]
    anomalies: List[float] = []
    for i in range(1, len(counts)):
        prev = counts[i - 1][1]
        curr = counts[i][1]
        if prev and abs(curr - prev) / prev > 0.5:
            anomalies.append(counts[i][0])
    return anomalies


# ---------------------------------------------------------------------------
# Social network analysis
# ---------------------------------------------------------------------------


def informal_power_structure(graph: GraphModel | nx.Graph, top_k: int = 5) -> List[str]:
    """Identify influential individuals via eigenvector centrality."""

    scores = eigenvector_centrality_scores(graph)
    return [
        n
        for n, _ in sorted(scores.items(), key=lambda item: item[1], reverse=True)[
            :top_k
        ]
    ]


def detect_unusual_collaborations(
    graph: GraphModel | nx.Graph,
) -> List[Tuple[str, str]]:
    """Edges with weights significantly above the mean."""

    G = _to_nx(graph)
    weights = [d.get("weight", 1.0) for _, _, d in G.edges(data=True)]
    if not weights:
        return []
    threshold = mean(weights) + stdev(weights)
    return [
        (u, v) for u, v, d in G.edges(data=True) if d.get("weight", 1.0) > threshold
    ]


def find_hidden_relationships(graph: GraphModel | nx.Graph) -> List[Tuple[str, str]]:
    """Pairs of nodes sharing many neighbours but lacking a direct edge."""

    G = _to_nx(graph)
    hidden: List[Tuple[str, str]] = []
    undirected = G.to_undirected()
    for u, v in combinations(G.nodes(), 2):
        if undirected.has_edge(u, v):
            continue
        common = len(nx.common_neighbors(undirected, u, v))
        if common > 2:
            hidden.append((u, v))
    return hidden


# ---------------------------------------------------------------------------
# Behavioural cliques and coordinated behaviour
# ---------------------------------------------------------------------------


def behavioral_cliques(graph: GraphModel | nx.Graph) -> List[List[str]]:
    """Return cliques of users with similar access patterns."""

    G = _to_nx(graph).to_undirected()
    return [list(c) for c in nx.find_cliques(G)]


def detect_coordinated_behavior(graph: GraphModel | nx.Graph) -> List[set]:
    """Groups of nodes with identical neighbour sets."""

    G = _to_nx(graph)
    signature: Dict[Tuple[str, ...], set] = defaultdict(set)
    for node in G.nodes():
        neighbours = tuple(sorted(G.neighbors(node)))
        signature[neighbours].add(node)
    return [nodes for nodes in signature.values() if len(nodes) > 1]


def deviation_from_group_norms(
    graph: GraphModel | nx.Graph, communities: Iterable[Iterable[str]]
) -> List[str]:
    """Nodes deviating from group degree means by more than two standard deviations."""

    G = _to_nx(graph)
    outliers: List[str] = []
    for community in communities:
        degrees = [G.degree(n) for n in community]
        if len(degrees) < 2:
            continue
        m = mean(degrees)
        s = stdev(degrees)
        if s:
            outliers.extend(n for n, d in zip(community, degrees) if abs(d - m) > 2 * s)
    return outliers


# ---------------------------------------------------------------------------
# Risk propagation
# ---------------------------------------------------------------------------


def _propagate(
    graph: GraphModel | nx.Graph,
    initial: Dict[str, float],
    decay: float,
) -> Dict[str, float]:
    G = _to_nx(graph)
    scores = initial.copy()
    frontier = list(initial.keys())
    while frontier:
        node = frontier.pop(0)
        for neighbor in G.neighbors(node):
            propagated = scores[node] * decay
            if propagated <= 0.0:
                continue
            if propagated > scores.get(neighbor, 0.0):
                scores[neighbor] = propagated
                frontier.append(neighbor)
    return scores


def risk_propagation(
    graph: GraphModel | nx.Graph, initial_risk: Dict[str, float], decay: float = 0.5
) -> Dict[str, float]:
    """Propagate risk scores through the network."""

    return _propagate(graph, initial_risk, decay)


def trust_degradation(
    graph: GraphModel | nx.Graph, initial_trust: Dict[str, float], decay: float = 0.1
) -> Dict[str, float]:
    """Propagate trust degradation across connections."""

    return _propagate(graph, initial_trust, decay)


def insider_threat_propagation(
    graph: GraphModel | nx.Graph, suspects: Dict[str, float], decay: float = 0.3
) -> Dict[str, float]:
    """Propagate insider threat scores starting from ``suspects``."""

    return _propagate(graph, suspects, decay)
