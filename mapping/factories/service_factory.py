from __future__ import annotations

from typing import TYPE_CHECKING, Any

from core.container import container as default_container
from mapping.models import (
    HeuristicMappingModel,
    MappingModel,
    load_model_from_config,
)
from mapping.processors.ai_processor import AIColumnMapperAdapter
from mapping.processors.column_processor import ColumnProcessor
from mapping.processors.device_processor import DeviceProcessor
from mapping.service import MappingService
from mapping.storage.base import JsonStorage, MemoryStorage

if TYPE_CHECKING:  # pragma: no cover - only for type hints
    from yosai_intel_dashboard.src.services.learning.src.api.coordinator import LearningCoordinator


def create_learning_service(
    path: str | None = None, in_memory: bool = False
) -> "LearningCoordinator":
    from yosai_intel_dashboard.src.services.learning.src.api.coordinator import LearningCoordinator

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
    *,
    model_key: str | None = None,
    config_path: str | None = None,
    container: Any | None = None,
) -> MappingService:
    container = container or default_container
    in_memory = storage_type == "memory"
    learning = create_learning_service(in_memory=in_memory)

    if enable_ai:
        key = model_key or "default"
        svc_key = f"mapping_model:{key}"
        if config_path and not container.has(svc_key):
            model: MappingModel = load_model_from_config(config_path)
            container.register_singleton(svc_key, model, protocol=MappingModel)
        elif not container.has(svc_key):
            container.register_singleton(
                svc_key, HeuristicMappingModel(), protocol=MappingModel
            )
        ai_adapter = AIColumnMapperAdapter(container=container, default_model=key)
    else:
        ai_adapter = None

    column_proc = ColumnProcessor(
        ai_adapter, container=container, default_model=model_key or "default"
    )

    device_proc = DeviceProcessor()
    return MappingService(learning.storage, column_proc, device_proc)
