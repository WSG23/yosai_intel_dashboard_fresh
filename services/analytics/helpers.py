from __future__ import annotations

import logging
from typing import Any, Dict, TYPE_CHECKING

import pandas as pd
from core.protocols import (
    ConfigurationProtocol,
    DatabaseProtocol,
    EventBusProtocol,
    StorageProtocol,
)
from services.analytics.calculator import Calculator
from services.analytics.data.loader import DataLoader
from services.analytics.orchestrator import AnalyticsOrchestrator
from services.analytics.protocols import DataProcessorProtocol
from services.analytics.publisher import Publisher
from services.analytics.upload_analytics import UploadAnalyticsProcessor
from services.analytics_summary import generate_sample_analytics
from services.controllers.upload_controller import UploadProcessingController
from services.data_processing.processor import Processor
from services.database_retriever import DatabaseAnalyticsRetriever
from services.interfaces import get_upload_data_service
from services.summary_report_generator import SummaryReportGenerator
from services.upload_data_service import UploadDataService
from validation.security_validator import SecurityValidator

if TYPE_CHECKING:  # pragma: no cover - for type checking only
    from yosai_intel_dashboard.models.ml import ModelRegistry
    from .analytics_service import AnalyticsService

logger = logging.getLogger(__name__)


class DataSourceRouter:
    """Helper to route analytics requests based on source."""

    def __init__(self, orchestrator: AnalyticsOrchestrator) -> None:
        self.orchestrator = orchestrator

    def get_analytics(self, source: str) -> Dict[str, Any]:
        """Return analytics data for ``source``."""
        try:
            uploaded_data = self.orchestrator.loader.load_uploaded_data()
            if uploaded_data and source in ["uploaded", "sample"]:
                logger.info("Forcing uploaded data usage (source was: %s)", source)
                return self.orchestrator.process_uploaded_data_directly(uploaded_data)
        except (
            ImportError,
            FileNotFoundError,
            OSError,
            RuntimeError,
            ValueError,
            pd.errors.ParserError,
        ) as exc:
            logger.error(
                "Uploaded data check failed (%s): %s",
                type(exc).__name__,
                exc,
                exc_info=True,
            )
        if source == "sample":
            return generate_sample_analytics()
        if source == "uploaded":
            return {"status": "no_data", "message": "No uploaded files available"}
        if source == "database":
            return self.orchestrator.get_database_analytics()
        return {"status": "error", "message": f"Unknown source: {source}"}


def initialize_core_components(
    service: "AnalyticsService",
    database: DatabaseProtocol | None,
    data_processor: DataProcessorProtocol | None,
    config: ConfigurationProtocol | None,
    event_bus: EventBusProtocol | None,
    storage: StorageProtocol | None,
    upload_data_service: UploadDataService | None,
    model_registry: ModelRegistry | None,
    *,
    upload_controller: UploadProcessingController | None = None,
    upload_processor: UploadAnalyticsProcessor | None = None,
    report_generator: SummaryReportGenerator | None = None,
) -> None:
    """Initialize basic service dependencies."""

    service.database = database
    service.data_processor = data_processor or Processor(validator=SecurityValidator())
    service.config = config
    service.event_bus = event_bus
    service.storage = storage
    service.upload_data_service = upload_data_service or get_upload_data_service()
    service.model_registry = model_registry
    service.validation_service = SecurityValidator()
    if data_processor is None:
        service.processor = Processor(validator=service.validation_service)
        service.data_processor = service.processor
    else:
        service.processor = data_processor
        service.data_processor = data_processor
    service.data_loading_service = service.processor
    from services.data_processing.file_handler import FileHandler

    service.file_handler = FileHandler()

    if upload_processor is None:
        upload_processor = UploadAnalyticsProcessor(service.validation_service, service.processor)
    if upload_controller is None:
        service.upload_controller = UploadProcessingController(
            service.validation_service,
            service.processor,
            service.upload_data_service,
            upload_processor,
        )
    else:
        service.upload_controller = upload_controller
    service.upload_processor = upload_processor
    service.report_generator = report_generator or SummaryReportGenerator()


def initialize_orchestrator_components(
    service: "AnalyticsService",
    loader: DataLoader | None = None,
    calculator: Calculator | None = None,
    publisher: Publisher | None = None,
    db_retriever: DatabaseAnalyticsRetriever | None = None,
) -> None:
    """Initialize orchestrator helpers for the service."""

    service._setup_database(db_retriever)
    loader = loader or DataLoader(service.upload_controller, service.processor)
    calculator = calculator or Calculator(service.report_generator)
    publisher = publisher or Publisher(service.event_bus)
    service._create_orchestrator(loader, calculator, publisher)
    service.router = DataSourceRouter(service.orchestrator)


__all__ = [
    "DataSourceRouter",
    "initialize_core_components",
    "initialize_orchestrator_components",
]
