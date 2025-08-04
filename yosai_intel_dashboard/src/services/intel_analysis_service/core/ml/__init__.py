"""Graph machine learning utilities."""

from .embeddings import GraphSAGE, Node2Vec, GCN
from .attention_models import GraphAttentionNetwork
from .link_prediction import LinkPredictor
from .graph_classification import GraphClassifier
from .api import (
    train_embeddings,
    train_link_predictor,
    score_link,
    train_graph_classifier,
    classify_graph,
)

__all__ = [
    "Node2Vec",
    "GraphSAGE",
    "GCN",
    "GraphAttentionNetwork",
    "LinkPredictor",
    "GraphClassifier",
    "train_embeddings",
    "train_link_predictor",
    "score_link",
    "train_graph_classifier",
    "classify_graph",
]
