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


__all__ = [
    "AI_COLUMN_SERVICE_AVAILABLE",
    "AI_DOOR_SERVICE_AVAILABLE",
    "CONTAINER_AVAILABLE",
    "CONFIG_SERVICE_AVAILABLE",
    "DoorMappingService",
    "get_door_mapping_service",
    "ServiceContainer",
    "DynamicConfigurationService",
]
