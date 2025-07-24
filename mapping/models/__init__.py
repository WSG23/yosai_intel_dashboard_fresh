from __future__ import annotations

from typing import Dict, Type

from .base import MappingModel

_registry: Dict[str, Type[MappingModel]] = {}


def register_model(name: str, cls: Type[MappingModel]) -> None:
    """Register a mapping model class under ``name``."""
    _registry[name] = cls


def get_registered_model(name: str | None) -> Type[MappingModel]:
    if not name or name not in _registry:
        raise ValueError(f"Unknown mapping model: {name}")
    return _registry[name]


def load_model(path: str) -> MappingModel:
    """Load a mapping model from a YAML or JSON configuration file."""
    return MappingModel.load_from_config(path)


def reload_model(path: str) -> MappingModel:
    """Convenience helper for runtime switching."""
    model = load_model(path)
    return model

__all__ = ["MappingModel", "register_model", "get_registered_model", "load_model", "reload_model"]

# Register built-in models
from .rule_based import RuleBasedModel
register_model("rule_based", RuleBasedModel)

