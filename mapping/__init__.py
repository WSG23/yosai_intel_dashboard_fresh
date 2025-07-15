"""Public API for the mapping package."""

from .core.interfaces import (
    StorageInterface,
    ProcessorInterface,
    LearningInterface,
)
from .core.models import ProcessingResult, MappingData
from .service import MappingService


def create_mapping_service(*args, **kwargs):
    """Lazily import and delegate to the mapping service factory."""
    from .factories.service_factory import (
        create_mapping_service as _factory,
    )

    return _factory(*args, **kwargs)

__all__ = [
    "StorageInterface",
    "ProcessorInterface",
    "LearningInterface",
    "ProcessingResult",
    "MappingData",
    "MappingService",
    "create_mapping_service",
]
