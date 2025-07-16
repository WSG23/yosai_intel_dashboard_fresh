from __future__ import annotations

import logging
from typing import List, Tuple, Dict

import pandas as pd

from services.analytics.upload_analytics import UploadAnalyticsProcessor
from services.data_processing.processor import Processor

logger = logging.getLogger(__name__)


class DataLoader:
    """Load and verify uploaded or database data for analytics."""

    def __init__(
        self,
        upload_processor: UploadAnalyticsProcessor,
        processor: Processor,
        row_limit_warning: int,
        large_data_threshold: int,
    ) -> None:
        self.upload_processor = upload_processor
        self.processor = processor
        self.row_limit_warning = row_limit_warning
        self.large_data_threshold = large_data_threshold

    def load_patterns_data(self, data_source: str | None) -> Tuple[pd.DataFrame, int]:
        """Return cleaned dataframe and original row count for pattern analysis."""
        if data_source == "database":
            df, _meta = self.processor.get_processed_database()
            uploaded_data = {"database": df} if not df.empty else {}
        else:
            uploaded_data = self.upload_processor.load_uploaded_data()

        if not uploaded_data:
            return pd.DataFrame(), 0

        all_dfs: List[pd.DataFrame] = []
        total_original_rows = 0

        logger.info("\ud83d\udcc1 Found %s uploaded files", len(uploaded_data))

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
        return combined_df, total_original_rows

    def verify_combined_data(self, df: pd.DataFrame, original_rows: int) -> None:
        """Log sanity checks for the combined dataframe."""
        final_rows = len(df)
        logger.info("\ud83d\udcca COMBINED DATASET: %s total rows", f"{final_rows:,}")

        if final_rows != original_rows:
            logger.warning(
                "\u26a0\ufe0f  Data loss detected: %s \u2192 %s",
                f"{original_rows:,}",
                f"{final_rows:,}",
            )

        if (
            final_rows == self.row_limit_warning
            and original_rows > self.row_limit_warning
        ):
            logger.error(
                "\ud83d\udea8 FOUND %s ROW LIMIT in unique patterns analysis!",
                self.row_limit_warning,
            )
            logger.error("   Original rows: %s", f"{original_rows:,}")
            logger.error("   Final rows: %s", f"{final_rows:,}")
        elif final_rows > self.large_data_threshold:
            logger.info("\u2705 Processing large dataset: %s rows", f"{final_rows:,}")


__all__ = ["DataLoader"]
