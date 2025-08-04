from __future__ import annotations

"""Simple Neo4j client used for tests and lightweight integrations.

The client wraps the official Neo4j Python driver when available.  When no
connection details are supplied it falls back to an in-memory ``networkx``
representation which mimics a tiny subset of Neo4j functionality.  This
makes it suitable for unit tests where running a full database would be
impractical.
"""

from typing import Any, Iterable, Mapping, Dict

import networkx as nx

try:  # pragma: no cover - optional dependency
    from neo4j import GraphDatabase  # type: ignore
except Exception:  # pragma: no cover - handled dynamically
    GraphDatabase = None  # type: ignore


class Neo4jClient:
    """Utility for interacting with Neo4j or an in-memory substitute."""

    def __init__(self, uri: str | None = None, user: str | None = None, password: str | None = None) -> None:
        self.driver = None
        if uri and GraphDatabase is not None:  # pragma: no cover - requires neo4j server
            self.driver = GraphDatabase.driver(uri, auth=(user or "", password or ""))
        self.graph = nx.MultiDiGraph()

    # ------------------------------------------------------------------
    # Driver management
    # ------------------------------------------------------------------
    def close(self) -> None:
        if self.driver is not None:  # pragma: no cover - requires neo4j server
            self.driver.close()

    def run_cypher(self, query: str, parameters: Mapping[str, Any] | None = None):
        """Execute a Cypher query if a real driver is configured."""
        if self.driver is None:
            raise RuntimeError("Neo4j driver not initialised")
        with self.driver.session() as session:  # pragma: no cover - requires neo4j server
            return session.run(query, parameters or {})

    # ------------------------------------------------------------------
    # In-memory helpers used in tests
    # ------------------------------------------------------------------
    def add_node(self, node_id: str, **properties: Any) -> None:
        """Create or update a node in the backing store."""
        if self.driver is not None:  # pragma: no cover - requires neo4j server
            cypher = "MERGE (n {id: $id}) SET n += $props"
            self.run_cypher(cypher, {"id": node_id, "props": properties})
        else:
            self.graph.add_node(node_id, **properties)

    def add_edge(self, source: str, target: str, rel_type: str, **properties: Any) -> None:
        if self.driver is not None:  # pragma: no cover - requires neo4j server
            cypher = (
                f"MATCH (a {{id:$source}}),(b {{id:$target}}) "
                f"MERGE (a)-[r:{rel_type}]->(b) SET r += $props"
            )
            self.run_cypher(cypher, {"source": source, "target": target, "props": properties})
        else:
            self.graph.add_edge(source, target, key=rel_type, type=rel_type, **properties)

    def get_graph(self) -> nx.MultiDiGraph:
        """Return the entire graph as a :class:`networkx.MultiDiGraph`."""
        if self.driver is not None:  # pragma: no cover - requires neo4j server
            g = nx.MultiDiGraph()
            nodes = self.run_cypher("MATCH (n) RETURN n.id as id, n as data")
            for record in nodes:
                props = {k: v for k, v in record["data"].items() if k != "id"}
                g.add_node(record["id"], **props)
            edges = self.run_cypher(
                "MATCH (a)-[r]->(b) RETURN a.id as source, b.id as target, type(r) as type, r as data"
            )
            for record in edges:
                props = {k: v for k, v in record["data"].items()}
                g.add_edge(record["source"], record["target"], key=record["type"], type=record["type"], **props)
            return g
        return self.graph.copy()

    def write_node_embeddings(self, embeddings: Mapping[str, Iterable[float]]) -> None:
        """Persist node embeddings as the ``embedding`` property."""
        if self.driver is not None:  # pragma: no cover - requires neo4j server
            for node_id, emb in embeddings.items():
                self.run_cypher(
                    "MATCH (n {id:$id}) SET n.embedding = $emb",
                    {"id": node_id, "emb": list(map(float, emb))},
                )
        else:
            for node_id, emb in embeddings.items():
                if node_id in self.graph:
                    self.graph.nodes[node_id]["embedding"] = list(map(float, emb))

    def read_node_embeddings(self) -> Dict[str, list[float]]:
        """Return embeddings stored on nodes, if present."""
        if self.driver is not None:  # pragma: no cover - requires neo4j server
            result = self.run_cypher(
                "MATCH (n) WHERE exists(n.embedding) RETURN n.id as id, n.embedding as emb"
            )
            return {record["id"]: record["emb"] for record in result}
        return {
            str(node): data["embedding"]
            for node, data in self.graph.nodes(data=True)
            if "embedding" in data
        }
