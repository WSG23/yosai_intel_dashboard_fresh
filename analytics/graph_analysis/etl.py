"""Graph construction utilities.

This module provides helpers to construct and update graphs from access log
records.  The functions are intentionally lightweight so they can be easily
extended to a full ETL/streaming pipeline.
"""

from __future__ import annotations

from typing import Dict, Iterable, Tuple

import networkx as nx

from .schema import Edge, GraphModel, Node, NodeType


def build_graph_from_logs(access_logs: Iterable[Dict]) -> GraphModel:
    """Build a :class:`GraphModel` from an iterable of access log dictionaries.

    Each log entry is expected to contain ``person``, ``device``,
    ``access_point``, ``location`` and ``timestamp`` keys.
    """

    graph = GraphModel()
    for log in access_logs:
        person = Node(id=str(log["person"]), type=NodeType.PERSON)
        device = Node(id=str(log["device"]), type=NodeType.DEVICE)
        access_point = Node(id=str(log["access_point"]), type=NodeType.ACCESS_POINT)
        location = Node(id=str(log["location"]), type=NodeType.LOCATION)

        for node in (person, device, access_point, location):
            graph.add_node(node)

        graph.add_edge(
            Edge(
                source=person.id,
                target=access_point.id,
                relation="ACCESSED",
                timestamp=log.get("timestamp"),
            )
        )
        graph.add_edge(
            Edge(
                source=device.id,
                target=person.id,
                relation="BELONGS_TO",
                timestamp=log.get("timestamp"),
            )
        )
        graph.add_edge(
            Edge(
                source=access_point.id,
                target=location.id,
                relation="LOCATED_AT",
                timestamp=log.get("timestamp"),
            )
        )
    return graph


def incremental_update(graph: GraphModel, events: Iterable[Dict]) -> None:
    """Incrementally update ``graph`` with new log ``events``."""

    new_graph = build_graph_from_logs(events)
    graph.graph.update(new_graph.graph)


def resolve_entities(graph: GraphModel, resolver: Dict[str, Tuple[str, float]]) -> None:
    """Merge duplicate nodes based on a resolver mapping.

    ``resolver`` maps old node ids to ``(resolved_id, confidence)`` tuples.
    Only mappings with a confidence above 0.8 are applied.
    """

    relabel = {k: v for k, (v, score) in resolver.items() if score > 0.8 and k != v}
    if relabel:
        nx_graph = graph.graph
        nx.relabel_nodes(nx_graph, relabel, copy=False)


def snapshot_graph(graph: GraphModel, start: float, end: float) -> GraphModel:
    """Return a snapshot of ``graph`` within the provided time window."""

    snapshot = GraphModel()
    snapshot.graph = graph.get_subgraph_by_time(start, end)
    return snapshot
