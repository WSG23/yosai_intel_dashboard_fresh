"""Interface utilities for database backed analytics."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Tuple

import pandas as pd

if TYPE_CHECKING:  # pragma: no cover - only for type hints
    from mapping.service import MappingService

logger = logging.getLogger(__name__)


class AnalyticsDataAccessor:
    """Helper to load processed data and learned mappings."""

    def __init__(
        self,
        base_data_path: str = "data",
        mapping_service: MappingService | None = None,
    ) -> None:
        self.base_path = Path(base_data_path)
        self.mappings_file = self.base_path / "learned_mappings.json"
        self.session_storage = self.base_path.parent / "session_storage"
        if mapping_service is None:
            from mapping.factories.service_factory import create_mapping_service

            mapping_service = create_mapping_service()
        self.mapping_service = mapping_service

    def get_processed_database(self) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Return the combined DataFrame and metadata using learned mappings."""
        mappings_data = self._load_consolidated_mappings()
        uploaded_data = self._get_uploaded_data()
        if not uploaded_data:
            return pd.DataFrame(), {}
        combined_df, metadata = self._apply_mappings_and_combine(
            uploaded_data, mappings_data
        )
        return combined_df, metadata

    def _load_consolidated_mappings(self) -> Dict[str, Any]:
        """Load consolidated mappings from ``learned_mappings.json``."""
        try:
            if self.mappings_file.exists():
                with open(
                    self.mappings_file, "r", encoding="utf-8", errors="replace"
                ) as f:
                    return json.load(f)
            return {}
        except Exception as exc:  # pragma: no cover - best effort
            logger.error("Error loading mappings: %s", exc)
            return {}

    def _get_uploaded_data(self) -> Dict[str, pd.DataFrame]:
        """Retrieve uploaded data from the ``file_upload`` module."""
        try:
            from yosai_intel_dashboard.src.services.upload_data_service import (
                get_uploaded_data,
            )

            uploaded_data = get_uploaded_data()
            if uploaded_data:
                logger.info("Found %s uploaded files", len(uploaded_data))
                for filename, df in uploaded_data.items():
                    logger.info("%s: %s rows", filename, len(df))
                return uploaded_data
            logger.info("No uploaded data found")
            return {}
        except ImportError:
            logger.error("Could not import uploaded data from file_upload")
            return {}
        except Exception as exc:  # pragma: no cover - best effort
            logger.error("Error getting uploaded data: %s", exc)
            return {}

    def _apply_mappings_and_combine(
        self,
        uploaded_data: Dict[str, pd.DataFrame],
        mappings_data: Dict[str, Any],
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Apply learned mappings to each DataFrame and combine them."""
        combined_dfs = []
        metadata = {
            "total_files": len(uploaded_data),
            "processed_files": 0,
            "total_records": 0,
            "unique_users": set(),
            "unique_devices": set(),
            "date_range": {"start": None, "end": None},
        }

        for filename, df in uploaded_data.items():
            try:
                mapped_df = self._apply_column_mappings(df, filename, mappings_data)
                enriched_df = self._apply_device_mappings(
                    mapped_df, filename, mappings_data
                )
                enriched_df["source_file"] = filename
                enriched_df["processed_at"] = datetime.now()
                combined_dfs.append(enriched_df)
                metadata["processed_files"] += 1
                metadata["total_records"] += len(enriched_df)

                if "person_id" in enriched_df.columns:
                    metadata["unique_users"].update(
                        enriched_df["person_id"].dropna().unique()
                    )
                if "door_id" in enriched_df.columns:
                    metadata["unique_devices"].update(
                        enriched_df["door_id"].dropna().unique()
                    )

                if "timestamp" in enriched_df.columns:
                    dates = pd.to_datetime(
                        enriched_df["timestamp"], errors="coerce"
                    ).dropna()
                    if len(dates) > 0:
                        if metadata["date_range"]["start"] is None:
                            metadata["date_range"]["start"] = dates.min()
                            metadata["date_range"]["end"] = dates.max()
                        else:
                            metadata["date_range"]["start"] = min(
                                metadata["date_range"]["start"], dates.min()
                            )
                            metadata["date_range"]["end"] = max(
                                metadata["date_range"]["end"], dates.max()
                            )
            except Exception as exc:  # pragma: no cover - best effort
                logger.error("Error processing %s: %s", filename, exc)
                continue

        if combined_dfs:
            final_df = pd.concat(combined_dfs, ignore_index=True)
            metadata["unique_users"] = len(metadata["unique_users"])
            metadata["unique_devices"] = len(metadata["unique_devices"])
            return final_df, metadata

        return pd.DataFrame(), metadata

    def _apply_column_mappings(
        self, df: pd.DataFrame, filename: str, mappings_data: Dict[str, Any]
    ) -> pd.DataFrame:
        """Apply learned column mappings to *df*."""
        column_mappings = {}
        for mapping_info in mappings_data.values():
            if mapping_info.get("filename") == filename:
                column_mappings = mapping_info.get("column_mappings", {})
                break
        result = self.mapping_service.column_proc.process(df, filename)
        cleaned = result.data
        if column_mappings:
            cleaned = cleaned.rename(columns=column_mappings)
        return cleaned

    def _apply_device_mappings(
        self, df: pd.DataFrame, filename: str, mappings_data: Dict[str, Any]
    ) -> pd.DataFrame:
        """Apply learned device mappings to *df*."""
        if "door_id" not in df.columns:
            return df

        device_mappings = {}
        for fingerprint, mapping_info in mappings_data.items():
            if mapping_info.get("filename") == filename:
                device_mappings = mapping_info.get("device_mappings", {})
                break
        self.mapping_service.device_proc.process(df)
        if not device_mappings:
            return df

        device_attrs_df = pd.DataFrame.from_dict(device_mappings, orient="index")
        device_attrs_df.index.name = "door_id"
        device_attrs_df.reset_index(inplace=True)
        enriched_df = df.merge(device_attrs_df, on="door_id", how="left")
        return enriched_df
