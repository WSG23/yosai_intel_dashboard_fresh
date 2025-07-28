import logging

logger = logging.getLogger(__name__)

try:
    from services.data_enhancer.mapping_utils import get_ai_column_suggestions
    AI_COLUMN_SERVICE_AVAILABLE = True
    logger.info("✅ AI Column Service loaded successfully")
except Exception:  # pragma: no cover - optional dependency
    AI_COLUMN_SERVICE_AVAILABLE = False
    get_ai_column_suggestions = None
    logger.warning("⚠️ AI Column Service not available - using fallback")

try:
    from services.door_mapping_service import DoorMappingService
    from services.interfaces import get_door_mapping_service

    AI_DOOR_SERVICE_AVAILABLE = True
    logger.info("✅ AI Door Service loaded successfully")
except Exception as e:  # pragma: no cover - optional dependency
    DoorMappingService = None
    get_door_mapping_service = None
    AI_DOOR_SERVICE_AVAILABLE = False
    logger.warning(f"⚠️ AI Door Service not available - using fallback: {e}")

try:
    from core.service_container import ServiceContainer

    CONTAINER_AVAILABLE = True
    logger.info("✅ Service Container available")
except Exception:  # pragma: no cover - optional dependency
    CONTAINER_AVAILABLE = False
    ServiceContainer = None
    logger.warning("⚠️ Service Container not available")

try:
    from services.configuration_service import DynamicConfigurationService

    CONFIG_SERVICE_AVAILABLE = True
    logger.info("✅ Configuration Service available")
except Exception:  # pragma: no cover - optional dependency
    DynamicConfigurationService = None
    CONFIG_SERVICE_AVAILABLE = False
    logger.warning("⚠️ Configuration Service not available")

    from utils.config_resolvers import (
        resolve_ai_confidence_threshold,
        resolve_max_upload_size_mb,
        resolve_upload_chunk_size,
    )

    class FallbackConfigService:
        def get_ai_confidence_threshold(self) -> float:
            return resolve_ai_confidence_threshold()

        def get_max_upload_size_mb(self) -> int:
            return resolve_max_upload_size_mb()

        def get_upload_chunk_size(self) -> int:
            return resolve_upload_chunk_size()


__all__ = [
    "AI_COLUMN_SERVICE_AVAILABLE",
    "AI_DOOR_SERVICE_AVAILABLE",
    "CONTAINER_AVAILABLE",
    "CONFIG_SERVICE_AVAILABLE",
    "FallbackConfigService",
    "DoorMappingService",
    "get_door_mapping_service",
    "ServiceContainer",
    "DynamicConfigurationService",
]
