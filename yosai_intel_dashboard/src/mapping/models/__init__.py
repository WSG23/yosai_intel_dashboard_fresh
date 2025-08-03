"""Mapping model implementations and helpers."""

from __future__ import annotations

from typing import Dict, Type

from .base import MappingModel
from .heuristic import HeuristicMappingModel
from .rule_based import ColumnRules, RuleBasedModel, load_rules
import warnings


class MLMappingModel(HeuristicMappingModel):
    """Placeholder ML-based model using heuristics."""

    registry_name = "ml"


MODEL_REGISTRY: Dict[str, Type[MappingModel]] = MappingModel.REGISTRY


def get_registered_model(name: str) -> Type[MappingModel]:
    if name not in MODEL_REGISTRY:
        raise KeyError(f"Unknown model type: {name}")
    return MODEL_REGISTRY[name]


def load_model_from_config(path: str) -> MappingModel:
    return MappingModel.load_from_config(path)


# Backwards compatibility
def load_model(*args, **kwargs) -> MappingModel:
    warnings.warn(
        "load_model is deprecated; use load_model_from_config",
        DeprecationWarning,
        stacklevel=2,
    )
    return load_model_from_config(*args, **kwargs)

__all__ = [
    "ColumnRules",
    "load_rules",
    "MappingModel",
    "HeuristicMappingModel",
    "RuleBasedModel",
    "MLMappingModel",
    "get_registered_model",
    "load_model_from_config",
    "load_model",
    "MODEL_REGISTRY",
]
