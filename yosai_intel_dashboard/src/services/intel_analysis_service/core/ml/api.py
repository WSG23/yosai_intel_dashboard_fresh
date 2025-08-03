"""High level training and inference APIs for graph models."""
from __future__ import annotations

from typing import Mapping, Sequence, Tuple

import networkx as nx
import numpy as np

from .attention_models import GraphAttentionNetwork
from .embeddings import GraphSAGE, Node2Vec
from .graph_classification import GraphClassifier
from .link_prediction import LinkPredictor

ACCURACY_THRESHOLD = 0.9


def train_embeddings(
    graph: nx.Graph, method: str = "node2vec", **kwargs
) -> Node2Vec | GraphSAGE | GraphAttentionNetwork:
    """Train an embedding model on ``graph``.

    Parameters
    ----------
    graph:
        Graph to embed.
    method:
        One of ``"node2vec"``, ``"graphsage"`` or ``"gat"``.
    kwargs:
        Additional parameters forwarded to the underlying model.
    """
    if method == "node2vec":
        model = Node2Vec(**kwargs).fit(graph)
    elif method == "graphsage":
        model = GraphSAGE(**kwargs).fit(graph)
    elif method == "gat":
        features = kwargs.pop("features", None)
        if features is None:
            raise ValueError("features required for GAT training")
        model = GraphAttentionNetwork(**kwargs).fit(graph, features)
    else:
        raise ValueError(f"Unknown embedding method: {method}")
    return model


def train_link_predictor(
    graph: nx.Graph,
    edges: Sequence[Tuple[str, str]],
    labels: Sequence[int],
) -> Tuple[LinkPredictor, float, Mapping[str, np.ndarray]]:
    """Train a :class:`LinkPredictor` and ensure accuracy exceeds 90%."""
    embedder = Node2Vec().fit(graph)
    embeddings = embedder.get_embeddings()
    predictor = LinkPredictor().fit(embeddings, edges, labels)
    accuracy = predictor.evaluate(embeddings, edges, labels)
    if accuracy < ACCURACY_THRESHOLD:
        raise ValueError(
            f"Link prediction accuracy {accuracy:.2f} below {ACCURACY_THRESHOLD}"
        )
    return predictor, accuracy, embeddings


def score_link(
    predictor: LinkPredictor,
    embeddings: Mapping[str, np.ndarray],
    edge: Tuple[str, str],
) -> float:
    """Return the probability that ``edge`` exists."""
    return predictor.predict_proba(embeddings, edge)


def train_graph_classifier(
    graphs: Sequence[nx.Graph],
    labels: Sequence[int],
) -> Tuple[GraphClassifier, float]:
    """Train a :class:`GraphClassifier` and enforce a 90% accuracy threshold."""
    classifier = GraphClassifier().fit(graphs, labels)
    accuracy = classifier.evaluate(graphs, labels)
    if accuracy < ACCURACY_THRESHOLD:
        raise ValueError(
            f"Graph classification accuracy {accuracy:.2f} below {ACCURACY_THRESHOLD}"
        )
    return classifier, accuracy


def classify_graph(classifier: GraphClassifier, graph: nx.Graph) -> int:
    """Predict the class for ``graph`` using ``classifier``."""
    return classifier.predict([graph])[0]
