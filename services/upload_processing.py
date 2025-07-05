#!/usr/bin/env python3
"""Utilities for analytics over uploaded files."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd

from .analytics_summary import generate_basic_analytics, summarize_dataframe
from .chunked_analysis import analyze_with_chunking
from utils.mapping_helpers import map_and_clean

logger = logging.getLogger(__name__)


class UploadAnalyticsProcessor:
    """Handle analytics generation from uploaded datasets."""

    def __init__(
        self,
        file_processing_service: Any,
        validation_service: Any,
        data_loading_service: Any,
        input_validator: Any,
    ) -> None:
        self.file_processing_service = file_processing_service
        self.validation_service = validation_service
        self.data_loading_service = data_loading_service
        self.input_validator = input_validator

    def get_analytics_from_uploaded_data(self) -> Dict[str, Any]:
        """Generate analytics from uploaded files."""
        try:
            from services.upload_data_service import get_uploaded_filenames

            uploaded_files = get_uploaded_filenames()
            if not uploaded_files:
                return {"status": "no_data", "message": "No uploaded files available"}

            valid_files: List[str] = []
            processing_info: Dict[str, Any] = {}
            for path in uploaded_files:
                result = self.input_validator.validate_file_upload(path)
                if result.valid:
                    valid_files.append(path)
                else:
                    processing_info[path] = f"invalid: {result.message}"

            if not valid_files:
                return {
                    "status": "error",
                    "message": "No valid files to process",
                    "processing_info": processing_info,
                }

            (
                combined_df,
                info,
                processed_files,
                total_records,
            ) = self.file_processing_service.process_files(valid_files)
            if isinstance(info, list):
                processing_info["logs"] = info

            if combined_df.empty:
                return {
                    "status": "error",
                    "message": "No files could be processed successfully",
                    "processing_info": processing_info,
                }

            analytics = generate_basic_analytics(combined_df)
            analytics.update(
                {
                    "data_source": "uploaded_files_fixed",
                    "total_files_processed": processed_files,
                    "total_files_attempted": len(uploaded_files),
                    "processing_info": processing_info,
                    "total_events": total_records,
                    "active_users": combined_df["person_id"].nunique()
                    if "person_id" in combined_df.columns
                    else 0,
                    "active_doors": combined_df["door_id"].nunique()
                    if "door_id" in combined_df.columns
                    else 0,
                    "timestamp": datetime.now().isoformat(),
                }
            )
            return analytics
        except Exception as exc:  # pragma: no cover - best effort
            logger.error("Error getting analytics from uploaded data: %s", exc)
            return {"status": "error", "message": str(exc)}

    def _process_uploaded_data_directly(
        self, uploaded_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process uploaded files using streaming."""
        try:
            from collections import Counter
            from analytics.file_processing_utils import (
                stream_uploaded_file,
                aggregate_counts,
                build_result,
                calculate_date_range,
            )

            logger.info("Processing %d uploaded files directly...", len(uploaded_data))
            processing_info: Dict[str, Any] = {}
            total_events = 0
            user_counts: Counter[str] = Counter()
            door_counts: Counter[str] = Counter()
            min_ts: Optional[pd.Timestamp] = None
            max_ts: Optional[pd.Timestamp] = None

            for filename, source in uploaded_data.items():
                validation = self.input_validator.validate_file_upload(source)
                if not validation.valid:
                    processing_info[filename] = {
                        "rows": 0,
                        "status": f"invalid: {validation.message}",
                    }
                    continue
                try:
                    chunks = stream_uploaded_file(self.data_loading_service, source)
                    file_events, min_ts, max_ts = aggregate_counts(
                        chunks, user_counts, door_counts, min_ts, max_ts
                    )
                    processing_info[filename] = {"rows": file_events, "status": "ok"}
                    total_events += file_events
                except Exception as e:  # pragma: no cover - best effort
                    processing_info[filename] = {"rows": 0, "status": f"error: {e}"}
                    logger.error("Error processing %s: %s", filename, e)

            if not processing_info:
                return {"status": "error", "message": "No uploaded files processed"}

            date_range = calculate_date_range(min_ts, max_ts)
            result = build_result(
                total_events, user_counts, door_counts, date_range, processing_info
            )
            return result
        except Exception as exc:  # pragma: no cover - unexpected
            logger.error("Direct processing failed: %s", exc)
            return {"status": "error", "message": str(exc)}

    def load_uploaded_data(self) -> Dict[str, pd.DataFrame]:
        """Load uploaded data from file_upload page."""
        try:
            from services.upload_data_service import get_uploaded_data

            return get_uploaded_data() or {}
        except Exception as exc:  # pragma: no cover - best effort
            logger.error("Error loading uploaded data: %s", exc)
            return {}

    def clean_uploaded_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply standard column mappings and basic cleaning."""
        return map_and_clean(df)

    def summarize_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Create a summary dictionary from a combined DataFrame."""
        return summarize_dataframe(df)

    def analyze_with_chunking(
        self, df: pd.DataFrame, analysis_types: List[str]
    ) -> Dict[str, Any]:
        """Analyze a DataFrame using chunked processing."""
        return analyze_with_chunking(df, self.validation_service, analysis_types)

    def diagnose_data_flow(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Diagnostic helper for data flow."""
        logger.info("=== Data Flow Diagnosis ===")
        logger.info("Input DataFrame: %d rows, %d columns", len(df), len(df.columns))
        logger.info(
            "Memory usage: %.1f MB", df.memory_usage(deep=True).sum() / 1024 / 1024
        )
        validator = self.validation_service
        logger.info(
            "Validator config: upload_mb=%s, analysis_mb=%s, chunk_size=%s",
            validator.max_upload_mb,
            validator.max_analysis_mb,
            validator.chunk_size,
        )
        cleaned_df, needs_chunking = validator.validate_for_analysis(df.copy())
        logger.info(
            "After validation: %d rows, needs_chunking=%s",
            len(cleaned_df),
            needs_chunking,
        )
        if needs_chunking:
            chunk_size = validator.get_optimal_chunk_size(cleaned_df)
            logger.info("Optimal chunk size: %s", chunk_size)
        return {
            "input_rows": len(df),
            "validated_rows": len(cleaned_df),
            "needs_chunking": needs_chunking,
            "validator_config": {
                "max_upload_mb": validator.max_upload_mb,
                "max_analysis_mb": validator.max_analysis_mb,
                "chunk_size": validator.chunk_size,
            },
        }

    def _get_real_uploaded_data(self) -> Dict[str, Any]:
        """Load and summarize all uploaded records."""
        try:
            uploaded_data = self.load_uploaded_data()
            if not uploaded_data:
                return {"status": "no_data", "message": "No uploaded files available"}

            logger.info("Processing %d uploaded files...", len(uploaded_data))
            all_dfs: List[pd.DataFrame] = []
            total_original_rows = 0
            for filename, df in uploaded_data.items():
                logger.info("Processing %s: %d rows", filename, len(df))
                cleaned = self.clean_uploaded_dataframe(df)
                all_dfs.append(cleaned)
                total_original_rows += len(df)
            combined_df = pd.concat(all_dfs, ignore_index=True)
            logger.info("Combined: %d total rows", len(combined_df))
            summary = self.summarize_dataframe(combined_df)
            summary.update(
                {
                    "status": "success",
                    "timestamp": datetime.now().isoformat(),
                    "files_processed": len(uploaded_data),
                    "original_total_rows": total_original_rows,
                }
            )
            logger.info("Total Events: %d", summary["total_events"])
            logger.info("Active Users: %d", summary["active_users"])
            logger.info("Active Doors: %d", summary["active_doors"])
            return summary
        except Exception as exc:
            logger.error("Error processing uploaded data: %s", exc)
            return {
                "status": "error",
                "message": f"Error processing uploaded data: {str(exc)}",
                "total_events": 0,
            }

    def _get_analytics_with_fixed_processor(self) -> Dict[str, Any]:
        """Get analytics using the sample file processor."""
        from config.config import get_sample_files_config

        sample_cfg = get_sample_files_config()
        csv_file = os.getenv("SAMPLE_CSV_PATH", sample_cfg.csv_path)
        json_file = os.getenv("SAMPLE_JSON_PATH", sample_cfg.json_path)

        try:
            from services.data_processing.file_handler import FileHandler

            processor = FileHandler()
            all_data = []
            if os.path.exists(csv_file):
                df_csv = pd.read_csv(csv_file)
                result = processor._validate_data(df_csv)
                if result["valid"]:
                    processed_df = result["data"]
                    processed_df["source_file"] = "csv"
                    all_data.append(processed_df)
            if os.path.exists(json_file):
                with open(json_file, "r", encoding="utf-8", errors="replace") as f:
                    json_data = json.load(f)
                df_json = pd.DataFrame(json_data)
                result = processor._validate_data(df_json)
                if result["valid"]:
                    processed_df = result["data"]
                    processed_df["source_file"] = "json"
                    all_data.append(processed_df)
            if all_data:
                combined_df = pd.concat(all_data, ignore_index=True)
                return {
                    "status": "success",
                    "total_events": len(combined_df),
                    "active_users": combined_df["person_id"].nunique(),
                    "active_doors": combined_df["door_id"].nunique(),
                    "data_source": "fixed_processor",
                    "timestamp": datetime.now().isoformat(),
                }
        except Exception as exc:
            logger.error("Error in fixed processor analytics: %s", exc)
            return {"status": "error", "message": str(exc)}
        return {"status": "no_data", "message": "Files not available"}


__all__ = ["UploadAnalyticsProcessor"]
