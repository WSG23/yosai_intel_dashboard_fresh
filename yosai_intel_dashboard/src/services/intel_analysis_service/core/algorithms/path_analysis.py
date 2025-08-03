"""Path analysis utilities."""

from __future__ import annotations

from typing import Any, List

import networkx as nx


def shortest_path(
    graph: nx.Graph,
    source: Any,
    target: Any,
    weight: str | None = None,
) -> List[Any]:
    """Return the shortest path between *source* and *target*."""
    return nx.shortest_path(graph, source=source, target=target, weight=weight)


def k_hop_paths(graph: nx.Graph, source: Any, k: int) -> List[List[Any]]:
    """Enumerate simple paths of length *k* starting from *source*."""
    paths: List[List[Any]] = []

    def dfs(node: Any, depth: int, path: List[Any]) -> None:
        if depth == k:
            paths.append(path.copy())
            return
        for nbr in graph.neighbors(node):
            if nbr in path:
                continue
            path.append(nbr)
            dfs(nbr, depth + 1, path)
            path.pop()

    dfs(source, 0, [source])
    return paths


def temporal_path_exists(
    graph: nx.Graph,
    source: Any,
    target: Any,
    start_time,
    end_time,
    time_attr: str = "timestamp",
) -> bool:
    """Return True if path exists between *source* and *target* in the time range."""
    edges = [
        (u, v)
        for u, v, data in graph.edges(data=True)
        if time_attr in data and start_time <= data[time_attr] <= end_time
    ]
    if not edges:
        return False
    subgraph = graph.edge_subgraph(edges).copy()
    try:
        nx.shortest_path(subgraph, source, target)
        return True
    except nx.NetworkXNoPath:
        return False
