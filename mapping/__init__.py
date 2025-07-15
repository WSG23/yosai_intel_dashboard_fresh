"""Public API for the mapping package."""

from .core.interfaces import (
    StorageInterface,
    ProcessorInterface,
    LearningInterface,
)
from .core.models import ProcessingResult, MappingData
from .service import MappingService
from .factories.service_factory import create_mapping_service

__all__ = [
    "StorageInterface",
    "ProcessorInterface",
    "LearningInterface",
    "ProcessingResult",
    "MappingData",
    "MappingService",
    "create_mapping_service",
]
