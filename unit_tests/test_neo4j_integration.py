"""End-to-end tests for Neo4j powered graph workflows."""

import pathlib
import sys

# Add the services source tree to the module search path
sys.path.append(
    str(pathlib.Path(__file__).resolve().parents[1] / "yosai_intel_dashboard" / "src" / "services")
)

from graph.neo4j_client import Neo4jClient
from intel_analysis_service.core.ml.graph_classification import GraphClassifier
from intel_analysis_service.core.ml.embeddings import GCN


def _build_normal_graph(client: Neo4jClient):
    client.add_node("user1", label="Person")
    client.add_node("device1", label="Device")
    client.add_edge("user1", "device1", "ACCESSED")
    return client.get_graph()


def _build_anomalous_graph(client: Neo4jClient):
    client.add_node("user1", label="Person")
    client.add_node("device1", label="Device")
    client.add_node("device2", label="Device")
    client.add_edge("user1", "device1", "ACCESSED")
    client.add_edge("user1", "device2", "ACCESSED")
    return client.get_graph()


def test_neo4j_relationship_alerts() -> None:
    client = Neo4jClient()
    g_normal = _build_normal_graph(client)
    client.graph.clear()
    g_anom = _build_anomalous_graph(client)

    classifier = GraphClassifier(embedder=GCN(dimensions=4), neo4j_client=client)
    classifier.fit([g_normal, g_anom], [0, 1])

    # Ingest new events and classify directly from Neo4j
    client.graph.clear()
    _ = _build_anomalous_graph(client)
    prediction = classifier.predict_from_neo4j()[0]
    assert prediction == 1

    # Embeddings should have been written back to Neo4j
    embeddings = client.read_node_embeddings()
    assert "user1" in embeddings
