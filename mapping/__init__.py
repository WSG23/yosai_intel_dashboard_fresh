"""Public API for the mapping package."""

from .core.interfaces import (
    LearningInterface,
    ProcessorInterface,
    StorageInterface,
)
from .core.models import MappingData, ProcessingResult
from .models import (
    HeuristicMappingModel,
    MappingModel,
    MLMappingModel,
    load_model_from_config,
)
from .service import MappingService


def create_mapping_service(*args, **kwargs):
    """Lazily import and delegate to the mapping service factory."""
    from .factories.service_factory import create_mapping_service as _factory

    return _factory(*args, **kwargs)


__all__ = [
    "StorageInterface",
    "ProcessorInterface",
    "LearningInterface",
    "ProcessingResult",
    "MappingData",
    "MappingService",
    "create_mapping_service",
    "MappingModel",
    "HeuristicMappingModel",
    "MLMappingModel",
    "load_model_from_config",
]
