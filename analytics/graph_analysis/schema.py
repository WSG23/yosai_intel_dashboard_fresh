"""Graph data model for security intelligence analysis.

This module defines node and edge representations along with a container
`GraphModel` that uses a :class:`networkx.MultiDiGraph` to store
relationships.  Nodes and edges can carry arbitrary attributes including
weights and timestamps enabling temporal analysis.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional

import networkx as nx


class NodeType(str, Enum):
    """Supported node types in the security graph."""

    PERSON = "Person"
    LOCATION = "Location"
    DEVICE = "Device"
    ACCESS_POINT = "AccessPoint"
    DEPARTMENT = "Department"
    ROLE = "Role"


@dataclass
class Node:
    """A node in the graph."""

    id: str
    type: NodeType
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Edge:
    """A relationship between two nodes."""

    source: str
    target: str
    relation: str
    timestamp: Optional[float] = None
    weight: float = 1.0
    properties: Dict[str, Any] = field(default_factory=dict)


class GraphModel:
    """Wrapper around :class:`~networkx.MultiDiGraph` supporting temporal queries."""

    def __init__(self) -> None:
        self.graph = nx.MultiDiGraph()

    def add_node(self, node: Node) -> None:
        """Add a node to the graph."""

        self.graph.add_node(node.id, type=node.type.value, **node.properties)

    def add_edge(self, edge: Edge) -> None:
        """Add an edge with temporal and weight attributes."""

        self.graph.add_edge(
            edge.source,
            edge.target,
            key=edge.relation,
            relation=edge.relation,
            timestamp=edge.timestamp,
            weight=edge.weight,
            **edge.properties,
        )

    def get_subgraph_by_time(self, start: float, end: float) -> nx.MultiDiGraph:
        """Return a subgraph containing edges within ``start`` and ``end`` timestamps."""

        edges = [
            (u, v, k, d)
            for u, v, k, d in self.graph.edges(keys=True, data=True)
            if d.get("timestamp") is not None and start <= d["timestamp"] <= end
        ]
        subgraph = nx.MultiDiGraph()
        subgraph.add_nodes_from(self.graph.nodes(data=True))
        subgraph.add_edges_from(edges)
        return subgraph
