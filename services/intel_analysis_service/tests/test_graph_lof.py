import pytest

pytest.importorskip("networkx")

import networkx as nx

from analytics.graph_analysis.algorithms import graph_lof


def test_graph_lof_empty_graph() -> None:
    G = nx.Graph()
    assert graph_lof(G) == {}


def test_graph_lof_single_node() -> None:
    G = nx.Graph()
    G.add_node("A")
    assert graph_lof(G) == {}
