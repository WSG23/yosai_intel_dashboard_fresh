from typing import Any, Dict

from .services.core_analytics_service import CoreAnalyticsService
from .services.ai_analytics_service import AIAnalyticsService
from .services.performance_analytics_service import PerformanceAnalyticsService
from .services.data_processing_service import DataProcessingService
from .callbacks.unified_callback_manager import UnifiedCallbackManager
from .utils.unicode_processor import UnicodeProcessor


class CentralizedAnalyticsManager:
    """Central coordinator for all analytics operations."""

    def __init__(self) -> None:
        self.core_service = CoreAnalyticsService()
        self.ai_service = AIAnalyticsService()
        self.performance_service = PerformanceAnalyticsService()
        self.data_processing_service = DataProcessingService()
        self.callback_manager = UnifiedCallbackManager()
        self.unicode_processor = UnicodeProcessor()

    def process_analytics_request(self, request_type: str, data: Any) -> Dict[str, Any]:
        """Route analytics requests to the appropriate service."""
        if request_type == "core":
            return self.core_service.process(data)
        if request_type == "ai":
            return self.ai_service.process(data)
        if request_type == "performance":
            return self.performance_service.process(data)
        if request_type == "data":
            return self.data_processing_service.process(data)
        raise ValueError(f"Unknown request type: {request_type}")

    def get_unified_metrics(self) -> Dict[str, Any]:
        """Aggregate metrics from all services."""
        metrics = {}
        metrics.update(self.core_service.get_metrics())
        metrics.update(self.ai_service.get_metrics())
        metrics.update(self.performance_service.get_metrics())
        metrics.update(self.data_processing_service.get_metrics())
        return metrics
