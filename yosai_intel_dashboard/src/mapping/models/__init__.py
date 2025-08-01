"""Mapping model implementations and helpers."""

from __future__ import annotations

from typing import Dict, Type

from .base import MappingModel
from .heuristic import HeuristicMappingModel
from .rule_based import ColumnRules, RuleBasedModel, load_rules


class MLMappingModel(HeuristicMappingModel):
    """Placeholder ML-based model using heuristics."""


_MODEL_REGISTRY: Dict[str, Type[MappingModel]] = {
    "heuristic": HeuristicMappingModel,
    "rule_based": RuleBasedModel,
    "ml": MLMappingModel,
}


def register_model(name: str, cls: Type[MappingModel]) -> None:
    _MODEL_REGISTRY[name] = cls


def get_registered_model(name: str) -> Type[MappingModel]:
    if name not in _MODEL_REGISTRY:
        raise KeyError(f"Unknown model type: {name}")
    return _MODEL_REGISTRY[name]


def load_model_from_config(path: str) -> MappingModel:
    return MappingModel.load_from_config(path)


# Backwards compatibility
load_model = load_model_from_config

__all__ = [
    "ColumnRules",
    "load_rules",
    "MappingModel",
    "HeuristicMappingModel",
    "RuleBasedModel",
    "MLMappingModel",
    "register_model",
    "get_registered_model",
    "load_model_from_config",
    "load_model",
]
