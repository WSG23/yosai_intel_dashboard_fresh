from __future__ import annotations

import pytest

pytest.importorskip("networkx")
pytest.importorskip("sklearn")

from yosai_intel_dashboard.src.services.analytics.graph_analysis import (
    GraphModel,
    Node,
    NodeType,
    build_graph_from_logs,
)
from yosai_intel_dashboard.src.services.analytics.graph_analysis.algorithms import (
    betweenness_centrality,
    graph_lof,
    louvain_communities,
    risk_propagation,
    shortest_path,
)


def _sample_logs():
    return [
        {
            "person": "alice",
            "device": "laptop1",
            "access_point": "door1",
            "location": "hq",
            "timestamp": 1.0,
        },
        {
            "person": "bob",
            "device": "laptop2",
            "access_point": "door1",
            "location": "hq",
            "timestamp": 2.0,
        },
        {
            "person": "alice",
            "device": "laptop1",
            "access_point": "door2",
            "location": "lab",
            "timestamp": 3.0,
        },
    ]


def test_build_graph_from_logs_creates_nodes_and_edges():
    graph = build_graph_from_logs(_sample_logs())
    assert "alice" in graph.graph
    assert ("alice", "door1") in graph.graph.edges()


def test_algorithms_basic():
    graph = build_graph_from_logs(_sample_logs())
    bc = betweenness_centrality(graph)
    assert bc["door1"] > 0
    communities = louvain_communities(graph)
    assert any("alice" in c for c in communities)
    path = shortest_path(graph, "alice", "door2")
    assert path[0] == "alice"
    scores = risk_propagation(graph, {"alice": 1.0})
    assert scores["door1"] < 1.0


def test_graph_lof_handles_small_graphs():
    empty_graph = GraphModel()
    assert graph_lof(empty_graph) == {}

    single = GraphModel()
    single.add_node(Node("a", NodeType.PERSON))
    assert graph_lof(single) == {}
