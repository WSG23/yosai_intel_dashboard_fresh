from __future__ import annotations

"""Graph database connectors and in-memory graph representation.

This module provides light-weight connectors for Neo4j and Amazon Neptune
alongside simple in-memory graph management built on top of ``networkx``.
It defines the node and edge classes used by the intel analysis service.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, ClassVar, DefaultDict, Dict, Optional

from collections import defaultdict

import networkx as nx
import requests

try:  # pragma: no cover - optional dependency
    from neo4j import GraphDatabase
except Exception:  # pragma: no cover - handled at runtime
    GraphDatabase = None


# ---------------------------------------------------------------------------
# Node definitions
# ---------------------------------------------------------------------------


@dataclass
class Node:
    """Base node class used for all graph nodes."""

    id: str
    properties: Dict[str, Any] = field(default_factory=dict)

    # subclasses should override ``label``
    label: ClassVar[str] = "Node"

    def to_dict(self) -> Dict[str, Any]:
        """Return a serialisable representation of the node."""
        data = dict(self.properties)
        data["label"] = self.label
        return data


@dataclass
class Person(Node):
    label: ClassVar[str] = "Person"


@dataclass
class Location(Node):
    label: ClassVar[str] = "Location"


@dataclass
class Device(Node):
    label: ClassVar[str] = "Device"


@dataclass
class AccessPoint(Node):
    label: ClassVar[str] = "AccessPoint"


@dataclass
class Department(Node):
    label: ClassVar[str] = "Department"


@dataclass
class Role(Node):
    label: ClassVar[str] = "Role"


# ---------------------------------------------------------------------------
# Edge definitions
# ---------------------------------------------------------------------------


class EdgeType(str, Enum):
    ACCESSED = "ACCESSED"
    WORKS_WITH = "WORKS_WITH"
    MANAGES = "MANAGES"
    LOCATED_AT = "LOCATED_AT"
    BELONGS_TO = "BELONGS_TO"


@dataclass
class Edge:
    """Representation of an edge between two nodes."""

    source: str
    target: str
    type: EdgeType
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    weight: float = 1.0
    properties: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Return edge properties for storage."""
        data = dict(self.properties)
        data["type"] = self.type.value
        data["weight"] = self.weight
        if self.start_time is not None:
            data["start_time"] = self.start_time.isoformat()
        if self.end_time is not None:
            data["end_time"] = self.end_time.isoformat()
        return data


# ---------------------------------------------------------------------------
# Graph management
# ---------------------------------------------------------------------------


class GraphDB:
    """Manage one or more graphs backed by ``networkx``.

    The graphs are stored in-memory as ``MultiDiGraph`` instances.  Named
    graphs allow callers to separate concerns such as access control vs
    organisational structure.
    """

    def __init__(self, connector: Optional[object] = None) -> None:
        self.graphs: DefaultDict[str, nx.MultiDiGraph] = defaultdict(nx.MultiDiGraph)
        self.connector = connector

    def add_node(self, node: Node, graph: str = "default") -> None:
        g = self.graphs[graph]
        g.add_node(node.id, **node.to_dict())

    def add_edge(self, edge: Edge, graph: str = "default") -> None:
        g = self.graphs[graph]
        g.add_edge(edge.source, edge.target, key=edge.type.value, **edge.to_dict())

    def get_graph(self, name: str = "default") -> nx.MultiDiGraph:
        return self.graphs[name]


# ---------------------------------------------------------------------------
# Connectors
# ---------------------------------------------------------------------------


class Neo4jConnector:
    """Thin wrapper around the official Neo4j driver."""

    def __init__(self, uri: str, user: str, password: str) -> None:
        if GraphDatabase is None:  # pragma: no cover
            raise ImportError("neo4j driver is not installed")
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def run(self, query: str, parameters: Optional[Dict[str, Any]] = None):
        with self.driver.session() as session:
            return session.run(query, parameters or {})

    def close(self) -> None:
        self.driver.close()


class NeptuneConnector:
    """Simple HTTP Gremlin connector for Amazon Neptune."""

    def __init__(self, endpoint: str, port: int = 8182, protocol: str = "http") -> None:
        self.url = f"{protocol}://{endpoint}:{port}/gremlin"

    def run_gremlin(self, query: str, params: Optional[Dict[str, Any]] = None):
        payload: Dict[str, Any] = {"gremlin": query}
        if params:
            payload["bindings"] = params
        response = requests.post(self.url, json=payload)
        response.raise_for_status()
        return response.json()

