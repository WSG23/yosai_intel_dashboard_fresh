"""Enhanced AI Classification Plugin with CSV Processing"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from core.protocols.plugin import PluginMetadata

from .config import AIClassificationConfig, get_ai_config
from .database.csv_storage import CSVStorageRepository
from .services.column_mapper import ColumnMappingService
from .services.csv_processor import CSVProcessorService
from .services.entry_classifier import EntryClassificationService
from .services.floor_estimator import FloorEstimationService
from .services.japanese_handler import JapaneseTextHandler

logger = logging.getLogger(__name__)


class AIClassificationPlugin:
    """Enhanced plugin implementing CSV related services"""

    metadata = PluginMetadata(
        name="ai_classification",
        version="1.0.0",
        description="AI classification and CSV processing services",
        author="Yōsai",
    )

    def __init__(self, config: Optional[AIClassificationConfig] = None) -> None:
        self.config = config or get_ai_config()
        self.is_started = False
        self.services: Dict[str, Any] = {}

        # Database repository
        self.csv_repository: Optional[CSVStorageRepository] = None

        # Core services
        self.csv_processor: Optional[CSVProcessorService] = None
        self.column_mapper: Optional[ColumnMappingService] = None
        self.floor_estimator: Optional[FloorEstimationService] = None
        self.entry_classifier: Optional[EntryClassificationService] = None
        self.japanese_handler: Optional[JapaneseTextHandler] = None

    def start(self) -> bool:
        """Initialize plugin and services"""
        if self.is_started:
            logger.warning("plugin already started")
            return True
        try:
            # Repositories
            self.csv_repository = CSVStorageRepository(self.config.database.csv_path)
            if not self.csv_repository.initialize():
                raise RuntimeError("csv repository init failed")

            # Helper services
            self.japanese_handler = JapaneseTextHandler(self.config.japanese)
            self.csv_processor = CSVProcessorService(
                self.csv_repository,
                self.japanese_handler,
                self.config.csv_processing,
            )
            self.column_mapper = ColumnMappingService(
                self.csv_repository, self.config.column_mapping
            )
            self.floor_estimator = FloorEstimationService(
                self.csv_repository, self.config.floor_estimation
            )
            self.entry_classifier = EntryClassificationService(
                self.csv_repository, self.config.entry_classification
            )

            self._register_services()
            self.is_started = True
            logger.info("AIClassification plugin started")
            return True
        except Exception as exc:
            logger.error("failed to start plugin: %s", exc)
            return False

    def _register_services(self) -> None:
        self.services = {
            "process_csv": self.process_csv_file,
            "map_columns": self.map_columns,
            "confirm_mapping": self.confirm_column_mapping,
            "estimate_floors": self.estimate_floors,
            "classify_entries": self.classify_entries,
            "confirm_device_mapping": self.confirm_device_mapping,
            "get_session_data": self.get_session_data,
            "save_permanent_data": self.save_permanent_data,
        }

    # Service wrappers
    def process_csv_file(
        self, file_path: str, session_id: str, client_id: str = "default"
    ) -> Dict[str, Any]:
        if not self.csv_processor:
            raise RuntimeError("service not started")
        return self.csv_processor.process_file(file_path, session_id, client_id)

    def map_columns(self, headers: List[str], session_id: str) -> Dict[str, Any]:
        if not self.column_mapper:
            raise RuntimeError("service not started")
        return self.column_mapper.map_columns(headers, session_id)

    def confirm_column_mapping(self, mapping: Dict[str, str], session_id: str) -> bool:
        if not self.column_mapper:
            raise RuntimeError("service not started")
        return self.column_mapper.confirm_mapping(mapping, session_id)

    def estimate_floors(self, data: List[Dict], session_id: str) -> Dict[str, Any]:
        if not self.floor_estimator:
            raise RuntimeError("service not started")
        return self.floor_estimator.estimate_floors(data, session_id)

    def classify_entries(self, data: List[Dict], session_id: str) -> List[Dict]:
        if not self.entry_classifier:
            raise RuntimeError("service not started")
        return self.entry_classifier.classify_entries(data, session_id)

    def confirm_device_mapping(
        self, mappings: Dict[str, Dict], session_id: str
    ) -> bool:
        if not self.entry_classifier:
            raise RuntimeError("service not started")
        return self.entry_classifier.confirm_device_mapping(mappings, session_id)

    def get_session_data(self, session_id: str) -> Optional[Dict]:
        if not self.csv_repository:
            return None
        return self.csv_repository.get_session_data(session_id)

    def save_permanent_data(self, session_id: str, client_id: str) -> bool:
        if not self.csv_repository:
            return False
        return self.csv_repository.save_permanent_data(session_id, client_id)
