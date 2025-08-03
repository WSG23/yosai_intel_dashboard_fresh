"""Simple entity resolution for graph nodes.

Nodes with the same ``name`` property are merged together. A confidence score is
maintained and aliases for merged identifiers are recorded.
"""

from __future__ import annotations

from typing import Dict, List

from .graph_models import NodeMutation


class EntityResolver:
    """Resolve duplicate entities in a list of :class:`NodeMutation` objects."""

    def resolve(self, nodes: List[NodeMutation]) -> List[NodeMutation]:
        merged: Dict[str, NodeMutation] = {}
        for node in nodes:
            key = node.properties.get("name") or node.node_id
            if key in merged:
                existing = merged[key]
                aliases = existing.properties.setdefault("aliases", [existing.node_id])
                aliases.append(node.node_id)
                existing.properties.update(node.properties)
                existing.properties["confidence"] = min(
                    1.0, existing.properties.get("confidence", 0.8) + 0.1
                )
            else:
                props = dict(node.properties)
                props["confidence"] = 0.8
                merged[key] = NodeMutation(node.node_id, props, node.version)
        return list(merged.values())
