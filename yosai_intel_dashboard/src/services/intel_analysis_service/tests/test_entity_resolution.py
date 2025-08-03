from __future__ import annotations

import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from core.graph_entity_resolution import EntityResolver  # noqa: E402
from core.graph_models import NodeMutation  # noqa: E402


def test_entity_resolution_merges_nodes():
    resolver = EntityResolver()
    nodes = [
        NodeMutation("1", {"name": "alice"}),
        NodeMutation("2", {"name": "alice"}),
    ]
    resolved = resolver.resolve(nodes)
    assert len(resolved) == 1
    node = resolved[0]
    assert set(node.properties["aliases"]) == {"1", "2"}
    assert node.properties["confidence"] > 0.8
