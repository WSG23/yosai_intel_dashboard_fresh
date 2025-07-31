from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Tuple

import pandas as pd

from core.protocols import FileProcessorProtocol
from yosai_intel_dashboard.src.services.async_file_processor import AsyncFileProcessor
from yosai_intel_dashboard.src.services.data_enhancer.mapping_utils import get_ai_column_suggestions
from yosai_intel_dashboard.src.services.upload.file_processor_service import FileProcessor
from yosai_intel_dashboard.src.services.upload.learning_coordinator import LearningCoordinator
from components.ui_builder import UploadUIBuilder
from yosai_intel_dashboard.src.services.upload.protocols import (
    DeviceLearningServiceProtocol,
    UploadProcessingServiceProtocol,
    UploadStorageProtocol,
    UploadValidatorProtocol,
)
from yosai_intel_dashboard.src.services.upload_data_service import UploadDataService, UploadDataServiceProtocol
from validation.file_validator import FileValidator

logger = logging.getLogger(__name__)


class UploadOrchestrator(UploadProcessingServiceProtocol):
    """Coordinate validation, processing and UI generation."""

    def __init__(
        self,
        store: UploadStorageProtocol,
        learning_service: DeviceLearningServiceProtocol,
        data_service: UploadDataServiceProtocol | None = None,
        processor: FileProcessorProtocol | None = None,
        validator: UploadValidatorProtocol | None = None,
        ui_builder: UploadUIBuilder | None = None,
    ) -> None:
        self.store = store
        self.data_service = data_service or UploadDataService(store)
        self.processor = FileProcessor(
            store, processor or AsyncFileProcessor(), self.data_service
        )
        self.validator = FileValidator(validator)
        self.learner = LearningCoordinator(learning_service)
        self.ui = ui_builder or UploadUIBuilder()

    # ------------------------------------------------------------------
    async def process_uploaded_files(
        self,
        contents_list: List[str] | str,
        filenames_list: List[str] | str,
        *,
        task_progress: Callable[[int], None] | None = None,
        return_format: str = "legacy",
    ) -> Dict[str, Any] | Tuple:
        if not contents_list:
            return self._format_return(self._empty_result(), return_format)

        contents = self._ensure_list(contents_list)
        names = self._ensure_list(filenames_list)
        errors = self.validator.validate_files(contents, names)
        self.store.clear_all()
        parts = self._group_parts(contents, names)
        processed = await self.processor.process_files(parts, task_progress)
        result = self._assemble_result(processed, errors)
        return self._format_return(result, return_format)

    # ------------------------------------------------------------------
    def _ensure_list(self, value: List[str] | str) -> List[str]:
        return value if isinstance(value, list) else [value]

    def _group_parts(
        self, contents: List[str], names: List[str]
    ) -> Dict[str, List[str]]:
        grouped: Dict[str, List[str]] = {}
        for content, name in zip(contents, names):
            grouped.setdefault(name, []).append(content)
        return grouped

    def _empty_result(self) -> Dict[str, Any]:
        return {
            "upload_results": [],
            "file_info_dict": {},
            "current_file_info": {},
            "file_preview_components": [],
            "upload_nav": [],
            "metadata": {},
            "ai_suggestions": {},
            "device_mappings": {},
            "column_mappings": {},
            "validation_results": {},
            "processing_stats": {},
            "extensions": {},
        }

    def _assemble_result(
        self, processed: Dict[str, Dict[str, Any]], errors: Dict[str, str]
    ) -> Dict[str, Any]:
        result = self._empty_result()
        for fname, msg in errors.items():
            result["upload_results"].append(self.ui.build_failure_alert(msg))
            result["validation_results"][fname] = {"error": msg}
        for fname, info in processed.items():
            if "error" in info:
                result["upload_results"].append(
                    self.ui.build_failure_alert(
                        f"Error processing {fname}: {info['error']}"
                    )
                )
                result["validation_results"][fname] = {"error": info["error"]}
                continue
            self._add_file_result(result, fname, info)
        if result["file_info_dict"]:
            result["upload_nav"] = self.ui.build_navigation()
        result["processing_stats"] = self.ui.build_processing_stats(
            result["file_info_dict"]
        )
        return result

    def _add_file_result(
        self, result: Dict[str, Any], fname: str, info: Dict[str, Any]
    ) -> None:
        df = info["df"]
        rows = info["rows"]
        cols = info["cols"]
        result["upload_results"].append(self.ui.build_success_alert(fname, rows, cols))
        result["file_preview_components"].append(
            self.ui.build_file_preview_component(df, fname)
        )
        column_names = info["column_names"]
        file_info = {
            "filename": fname,
            "rows": rows,
            "columns": cols,
            "column_names": column_names,
            "upload_time": pd.Timestamp.now().isoformat(),
            "ai_suggestions": get_ai_column_suggestions(column_names),
        }
        result["file_info_dict"][fname] = file_info
        result["current_file_info"] = file_info
        result["ai_suggestions"][fname] = file_info["ai_suggestions"]
        result["column_mappings"][fname] = info.get("mapping", {})
        self._update_device_mappings(result, fname, df)

    def _update_device_mappings(
        self, result: Dict[str, Any], fname: str, df: pd.DataFrame
    ) -> None:
        user = self.learner.user_mappings(fname)
        if user:
            from yosai_intel_dashboard.src.services.ai_mapping_store import ai_mapping_store

            ai_mapping_store.clear()
            for dev, mapping in user.items():
                mapping["source"] = "user_confirmed"
                ai_mapping_store.set(dev, mapping)
            result["device_mappings"][fname] = user
            logger.info("✅ Loaded %s saved mappings - AI SKIPPED", len(user))
        else:
            from yosai_intel_dashboard.src.services.ai_mapping_store import ai_mapping_store

            ai_mapping_store.clear()
            self.learner.auto_apply(df, fname)
            result["device_mappings"][fname] = {}

    def _format_return(self, result: Dict[str, Any], return_format: str):
        if return_format == "dict":
            return result
        return result
