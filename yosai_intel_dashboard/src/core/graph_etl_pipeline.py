"""ETL pipeline that converts access logs into graph mutations."""

from __future__ import annotations

from typing import Iterable, List

from .graph_entity_resolution import EntityResolver
from .graph_models import EdgeMutation, NodeMutation
from .graph_versioning import GraphVersioner


class GraphETLPipeline:
    """Parse access logs and emit node/edge mutations with versioning."""

    def __init__(
        self,
        resolver: EntityResolver | None = None,
        versioner: GraphVersioner | None = None,
    ) -> None:
        self.resolver = resolver or EntityResolver()
        self.versioner = versioner or GraphVersioner()

    def parse_log_line(
        self, line: str
    ) -> tuple[List[NodeMutation], List[EdgeMutation]]:
        """Parse a single access log line.

        Expected format: ``timestamp,actor,target,action``.
        """

        parts = [p.strip() for p in line.split(",")]
        if len(parts) != 4:
            raise ValueError(
                "log line must have 4 comma-separated values:"
                " timestamp,actor,target,action"
            )
        timestamp, actor, target, action = parts
        nodes = [
            NodeMutation(actor, {"type": "actor", "name": actor}),
            NodeMutation(target, {"type": "target", "name": target}),
        ]
        edge_props = {"action": action, "timestamp": timestamp}
        edges = [EdgeMutation(actor, target, edge_props)]
        return nodes, edges

    def process_logs(self, logs: Iterable[str]):
        """Process an iterable of raw log lines and return a snapshot."""

        nodes: List[NodeMutation] = []
        edges: List[EdgeMutation] = []
        for line in logs:
            n, e = self.parse_log_line(line)
            nodes.extend(n)
            edges.extend(e)
        resolved_nodes = self.resolver.resolve(nodes)
        versioned_nodes = self.versioner.version_nodes(resolved_nodes)
        versioned_edges = self.versioner.version_edges(edges)
        return self.versioner.snapshot(versioned_nodes, versioned_edges)


__all__ = ["GraphETLPipeline"]

