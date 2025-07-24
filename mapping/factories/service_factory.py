from __future__ import annotations

from typing import TYPE_CHECKING

from mapping.storage.base import JsonStorage, MemoryStorage
from mapping.processors.ai_processor import AIColumnMapperAdapter
from mapping.processors.column_processor import ColumnProcessor
from mapping.processors.device_processor import DeviceProcessor
from mapping.service import MappingService
from mapping.models import MappingModel, load_model, RuleBasedModel
from core.service_container import ServiceContainer

if TYPE_CHECKING:  # pragma: no cover - only for type hints
from services.learning.src.api.coordinator import LearningCoordinator


def create_learning_service(
    path: str | None = None, in_memory: bool = False
) -> "LearningCoordinator":
    from services.learning.src.api.coordinator import LearningCoordinator

    storage = (
        MemoryStorage()
        if in_memory
        else JsonStorage(path or "data/learned_mappings.json")
    )
    return LearningCoordinator(storage)


def create_mapping_service(
    storage_type: str = "json",
    config_profile: str = "default",
    enable_ai: bool = True,
    model_config: str | None = None,
    ab_variant: str | None = None,
    container: ServiceContainer | None = None,
) -> MappingService:
    """Create :class:`MappingService` with optional mapping model registration."""

    in_memory = storage_type == "memory"
    learning = create_learning_service(in_memory=in_memory)
    container = container or ServiceContainer()

    # Load and register mapping model
    if model_config:
        model = load_model(model_config)
    else:
        model = RuleBasedModel()
    container.register_singleton("mapping_model", model, protocol=MappingModel)
    if ab_variant:
        container.register_singleton(f"mapping_model_{ab_variant.lower()}", model)

    ai_adapter = AIColumnMapperAdapter(container=container) if enable_ai else None
    column_proc = ColumnProcessor(ai_adapter)
    device_proc = DeviceProcessor()
    return MappingService(learning.storage, column_proc, device_proc)
