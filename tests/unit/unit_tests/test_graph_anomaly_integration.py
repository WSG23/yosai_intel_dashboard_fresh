"""End-to-end test for GraphAnomalyDetector using Neo4jClient."""

from __future__ import annotations

import pathlib
import sys

# Add services source tree to module search path
sys.path.insert(
    0,
    str(
        pathlib.Path(__file__).resolve().parents[1]
        / "yosai_intel_dashboard"
        / "src"
        / "services"
    ),
)

from graph.neo4j_client import Neo4jClient  # noqa: E402

from intel_analysis_service.core.ml.graph_anomaly import (  # noqa: E402
    GraphAnomalyDetector,
)


def test_end_to_end_anomaly_detection() -> None:
    client = Neo4jClient()
    detector = GraphAnomalyDetector(client, min_degree=3)

    users = [{"id": "u1"}, {"id": "u2"}]
    facilities = [{"id": "f1"}]
    devices = [{"id": "d1"}, {"id": "d2"}]
    events = [{"id": "e1"}, {"id": "e2"}]
    relationships = {
        "access": [("u1", "f1"), ("u2", "f1")],
        "contains": [("f1", "d1"), ("f1", "d2")],
        "generated": [("d1", "e1"), ("d2", "e1"), ("d1", "e2")],
        "triggered": [("u1", "e1"), ("u2", "e1"), ("u1", "e2")],
    }
    detector.load_entities(users, facilities, devices, events, relationships)

    graph = client.get_graph()
    # Ensure graph contains expected nodes and edges
    assert set(graph.nodes()) == {"u1", "u2", "f1", "d1", "d2", "e1", "e2"}
    assert ("d1", "e1") in {(u, v) for u, v, _ in graph.edges(keys=True)}

    anomalies = detector.detect_anomalies()
    if hasattr(anomalies, "__iter__") and not hasattr(anomalies, "iloc"):
        ids = {row["event_id"] for row in anomalies}
    else:
        ids = set(anomalies["event_id"])
    assert ids == {"e1"}
