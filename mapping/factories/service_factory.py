from __future__ import annotations

from typing import TYPE_CHECKING

from mapping.storage.base import JsonStorage, MemoryStorage
from mapping.processors.ai_processor import AIColumnMapperAdapter
from mapping.processors.column_processor import ColumnProcessor
from mapping.processors.device_processor import DeviceProcessor
from mapping.service import MappingService

if TYPE_CHECKING:  # pragma: no cover - only for type hints
    from services.learning.coordinator import LearningCoordinator


def create_learning_service(
    path: str | None = None, in_memory: bool = False
) -> "LearningCoordinator":
    from services.learning.coordinator import LearningCoordinator

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
) -> MappingService:
    in_memory = storage_type == "memory"
    learning = create_learning_service(in_memory=in_memory)
    ai_adapter = AIColumnMapperAdapter() if enable_ai else None
    column_proc = ColumnProcessor(ai_adapter)
    device_proc = DeviceProcessor()
    return MappingService(learning.storage, column_proc, device_proc)
