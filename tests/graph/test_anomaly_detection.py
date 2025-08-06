"""Service-level tests for graph anomaly detection."""

from __future__ import annotations

import pathlib
import sys

# Add services module to path
sys.path.insert(
    0,
    str(
        pathlib.Path(__file__).resolve().parents[2]
        / "yosai_intel_dashboard"
        / "src"
        / "services"
    )
)

from graph.neo4j_client import Neo4jClient  # noqa: E402

from intel_analysis_service.core.ml.graph_anomaly import (  # noqa: E402
    GraphAnomalyDetector,
)


def test_detects_high_degree_event() -> None:
    client = Neo4jClient()
    detector = GraphAnomalyDetector(client, min_degree=2)

    users = [{"id": "u1"}]
    facilities = [{"id": "f1"}]
    devices = [{"id": "d1"}, {"id": "d2"}]
    events = [{"id": "e1"}]
    relationships = {
        "access": [("u1", "f1")],
        "contains": [("f1", "d1"), ("f1", "d2")],
        "generated": [("d1", "e1"), ("d2", "e1")],
        "triggered": [("u1", "e1")],
    }
    detector.load_entities(users, facilities, devices, events, relationships)

    anomalies = detector.detect_anomalies()
    if hasattr(anomalies, "iloc"):
        assert not anomalies.empty
        assert anomalies.iloc[0]["event_id"] == "e1"
        assert anomalies.iloc[0]["degree"] == 3
    else:
        assert anomalies == [{"event_id": "e1", "degree": 3, "is_anomaly": True}]
