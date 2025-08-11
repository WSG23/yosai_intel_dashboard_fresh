from __future__ import annotations

import logging
from typing import Any, Dict, List, Tuple

import pandas as pd

from yosai_intel_dashboard.src.services.controllers.upload_controller import UploadProcessingController
from yosai_intel_dashboard.src.services.data_processing.processor import Processor
from yosai_intel_dashboard.src.core.interfaces import ConfigProviderProtocol

logger = logging.getLogger(__name__)



class DataLoader:
    """Load and prepare data for analytics operations."""

    def __init__(
        self,
        controller: UploadProcessingController,
        processor: Processor,
        config: ConfigProviderProtocol | None = None,
    ) -> None:
        self.controller = controller
        self.processor = processor
        self.upload_processor = controller.upload_processor
        self.config = config

    # ------------------------------------------------------------------
    # Delegated helpers
    # ------------------------------------------------------------------
    def load_uploaded_data(self) -> Dict[str, pd.DataFrame]:
        return self.controller.load_uploaded_data()

    def clean_uploaded_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        return self.controller.clean_uploaded_dataframe(df)

    def summarize_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]:
        summary = self.controller.summarize_dataframe(df)
        date_range = summary.get("date_range")
        if isinstance(date_range, dict):
            for key in ("start", "end"):
                value = date_range.get(key)
                if value and value != "Unknown":
                    dt = pd.to_datetime(value, utc=True)
                    # ensure Python datetime before ISO formatting
                    date_range[key] = dt.to_pydatetime().isoformat()
        return summary

    def analyze_with_chunking(
        self, df: pd.DataFrame, analysis_types: List[str]
    ) -> Dict[str, Any]:
        return self.controller.analyze_with_chunking(df, analysis_types)

    def diagnose_data_flow(self, df: pd.DataFrame) -> Dict[str, Any]:
        return self.controller.diagnose_data_flow(df)

    def get_real_uploaded_data(self) -> Dict[str, Any]:
        return self.controller.get_real_uploaded_data()

    def get_analytics_with_fixed_processor(self) -> Dict[str, Any]:
        return self.controller.get_analytics_with_fixed_processor()

    # ------------------------------------------------------------------
    # Pattern analysis helper
    # ------------------------------------------------------------------
    def load_patterns_dataframe(
        self, data_source: str | None
    ) -> Tuple[pd.DataFrame, int]:
        """Return dataframe and original row count for pattern analysis."""
        analytics_cfg = getattr(self.config, "analytics", None) if self.config else None
        row_warning = getattr(analytics_cfg, "row_limit_warning", 150)
        large_threshold = getattr(analytics_cfg, "large_data_threshold", 1000)
        if data_source == "database":
            df, _meta = self.processor.get_processed_database()
            uploaded_data = {"database": df} if not df.empty else {}
        else:
            uploaded_data = self.upload_processor.load_uploaded_data()

        if not uploaded_data:
            return pd.DataFrame(), 0

        all_dfs: List[pd.DataFrame] = []
        total_original_rows = 0

        logger.info("\U0001f4c1 Found %s uploaded files", len(uploaded_data))
        for filename, df in uploaded_data.items():
            original_rows = len(df)
            total_original_rows += original_rows
            logger.info("   %s: %s rows", filename, f"{original_rows:,}")

            cleaned_df = self.upload_processor.clean_uploaded_dataframe(df)
            all_dfs.append(cleaned_df)
            logger.info("   After cleaning: %s rows", f"{len(cleaned_df):,}")

        combined_df = (
            all_dfs[0] if len(all_dfs) == 1 else pd.concat(all_dfs, ignore_index=True)
        )

        final_rows = len(combined_df)
        logger.info("\U0001f4ca COMBINED DATASET: %s total rows", f"{final_rows:,}")

        if final_rows != total_original_rows:
            logger.warning(
                "\u26a0\ufe0f  Data loss detected: %s \u2192 %s",
                f"{total_original_rows:,}",
                f"{final_rows:,}",
            )

        if final_rows == row_warning and total_original_rows > row_warning:
            logger.error(
                "\U0001f6a8 FOUND %s ROW LIMIT in unique patterns analysis!",
                row_warning,
            )
            logger.error("   Original rows: %s", f"{total_original_rows:,}")
            logger.error("   Final rows: %s", f"{final_rows:,}")
        elif final_rows > large_threshold:
            logger.info("\u2705 Processing large dataset: %s rows", f"{final_rows:,}")

        return combined_df, total_original_rows


__all__ = ["DataLoader"]
