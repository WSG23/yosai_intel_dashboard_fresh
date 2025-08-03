import json
from datetime import datetime
from typing import Dict, List, Optional

import strawberry


@strawberry.type
class Node:
    id: strawberry.ID
    label: str
    properties: Optional[Dict[str, str]] = None


@strawberry.type
class Edge:
    source: strawberry.ID
    target: strawberry.ID
    weight: Optional[float] = None
    properties: Optional[Dict[str, str]] = None


@strawberry.type
class Graph:
    nodes: List[Node]
    edges: List[Edge]


# sample in-memory graph used for demonstration
SAMPLE_GRAPH = Graph(
    nodes=[
        Node(id="1", label="Person", properties={"name": "Alice"}),
        Node(id="2", label="Person", properties={"name": "Bob"}),
        Node(id="3", label="Place", properties={"name": "Mall"}),
    ],
    edges=[
        Edge(source="1", target="2", weight=1.0, properties={"type": "knows"}),
        Edge(source="2", target="3", weight=0.5, properties={"type": "visited"}),
    ],
)


def _filter_graph(
    label: Optional[str] = None,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
) -> Graph:
    # very small demo filter: only label filter is applied
    if label:
        nodes = [n for n in SAMPLE_GRAPH.nodes if n.label == label]
        ids = {n.id for n in nodes}
        edges = [e for e in SAMPLE_GRAPH.edges if e.source in ids and e.target in ids]
        return Graph(nodes=nodes, edges=edges)
    return SAMPLE_GRAPH


def _export_graph(graph: Graph, fmt: str) -> str:
    if fmt == "gephi":  # return GraphML/GEXF-like JSON for demo purposes
        data = {
            "graph": {
                "nodes": [node.__dict__ for node in graph.nodes],
                "edges": [edge.__dict__ for edge in graph.edges],
            }
        }
        return json.dumps(data)
    if fmt == "cytoscape":  # Cytoscape JSON format
        data = {
            "elements": {
                "nodes": [{"data": {"id": node.id, **(node.properties or {})}} for node in graph.nodes],
                "edges": [
                    {
                        "data": {
                            "source": edge.source,
                            "target": edge.target,
                            **(edge.properties or {}),
                        }
                    }
                    for edge in graph.edges
                ],
            }
        }
        return json.dumps(data)
    raise ValueError(f"Unknown export format: {fmt}")


@strawberry.type
class Query:
    graph: Graph = strawberry.field(resolver=_filter_graph)

    @strawberry.field
    def export_graph(self, info, format: str) -> str:  # noqa: A003 - `format` deliberate
        graph = _filter_graph()
        return _export_graph(graph, format.lower())


schema = strawberry.Schema(Query)
