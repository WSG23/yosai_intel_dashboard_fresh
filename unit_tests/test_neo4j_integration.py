"""End-to-end tests for Neo4j powered graph workflows."""

import pathlib
import sys

# Add the services source tree to the module search path
sys.path.append(
    str(pathlib.Path(__file__).resolve().parents[1] / "yosai_intel_dashboard" / "src" / "services")
)

import networkx as nx

from graph.neo4j_client import Neo4jClient
from intel_analysis_service.core.ml.graph_classification import GraphClassifier
from intel_analysis_service.core.ml.embeddings import GCN
def _build_normal_graph() -> nx.Graph:
    g = nx.Graph()
    g.add_node("user1", label="Person")
    g.add_node("device1", label="Device")
    g.add_edge("user1", "device1", type="ACCESSED")
    return g


def _build_anomalous_graph() -> nx.Graph:
    g = nx.Graph()
    g.add_node("user1", label="Person")
    g.add_node("device1", label="Device")
    g.add_node("device2", label="Device")
    g.add_edge("user1", "device1", type="ACCESSED")
    g.add_edge("user1", "device2", type="ACCESSED")
    return g


def test_neo4j_relationship_alerts() -> None:
    client = Neo4jClient()
    classifier = GraphClassifier(embedder=GCN(dimensions=4), neo4j_client=client)

    g_normal = _build_normal_graph()
    g_anom = _build_anomalous_graph()
    classifier.fit([g_normal, g_anom], [0, 1])

    # Ingest new events and classify directly from Neo4j
    client.graph.clear()
    classifier.write_graph_to_neo4j(g_anom)
    loaded = classifier.load_graph_from_neo4j()
    assert set(loaded.edges()) == set(g_anom.edges())
    prediction = classifier.predict_from_neo4j()[0]
    assert prediction == 1

    # Embeddings should have been written back to Neo4j
    embeddings = client.read_node_embeddings()
    assert "user1" in embeddings
