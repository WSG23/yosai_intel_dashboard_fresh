"""Graph versioning helpers."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from .graph_models import EdgeMutation, NodeMutation


class GraphVersioner:
    """Assign incremental versions to graph mutations and produce snapshots."""

    def __init__(self) -> None:
        self._node_version = 0
        self._edge_version = 0

    def version_nodes(self, nodes: List[NodeMutation]) -> List[NodeMutation]:
        for node in nodes:
            self._node_version += 1
            node.version = self._node_version
        return nodes

    def version_edges(self, edges: List[EdgeMutation]) -> List[EdgeMutation]:
        for edge in edges:
            self._edge_version += 1
            edge.version = self._edge_version
        return edges

    def snapshot(
        self, nodes: List[NodeMutation], edges: List[EdgeMutation]
    ) -> Dict[str, Any]:
        """Return a serialisable snapshot of the current graph state."""

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "nodes": [node.__dict__ for node in nodes],
            "edges": [edge.__dict__ for edge in edges],
        }
