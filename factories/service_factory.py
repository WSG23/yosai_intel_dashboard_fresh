from __future__ import annotations

from mapping.storage.base import JsonStorage, MemoryStorage
from processors.ai_processor import AIColumnMapperAdapter
from processors.column_processor import ColumnProcessor
from processors.device_processor import DeviceProcessor
from services.learning.coordinator import LearningCoordinator
from services.mapping_service import MappingService


def create_learning_service(path: str | None = None, in_memory: bool = False) -> LearningCoordinator:
    storage = MemoryStorage() if in_memory else JsonStorage(path or "data/learned_mappings.json")
    return LearningCoordinator(storage)


def create_mapping_service(in_memory: bool = False) -> MappingService:
    learning = create_learning_service(in_memory=in_memory)
    column_proc = ColumnProcessor(AIColumnMapperAdapter())
    device_proc = DeviceProcessor()
    return MappingService(learning.storage, column_proc, device_proc)
