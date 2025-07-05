"""DataFrame security validation with chunked processing support."""

import pandas as pd
from config.dynamic_config import dynamic_config
from config.constants import DataProcessingLimits
from plugins.service_locator import PluginServiceLocator

_unicode = PluginServiceLocator.get_unicode_handler()
UnicodeProcessor = _unicode.UnicodeProcessor
from core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)


class DataFrameSecurityValidator:
    """Validate DataFrames for safe processing with chunked analysis support."""

    def __init__(self):
        try:
            self.max_upload_mb = getattr(dynamic_config.security, "max_upload_mb", 500)
            self.max_analysis_mb = getattr(
                dynamic_config.security, "max_analysis_mb", 1000
            )
            if hasattr(dynamic_config, "analytics"):
                self.chunk_size = getattr(dynamic_config.analytics, "chunk_size", 50000)
            else:
                self.chunk_size = 50000

            logger.info(
                f"DataFrameValidator initialized: upload_limit={self.max_upload_mb}MB, analysis_limit={self.max_analysis_mb}MB, chunk_size={self.chunk_size}"
            )
        except Exception as e:
            logger.warning(f"Config loading failed, using defaults: {e}")
            self.max_upload_mb = 500
            self.max_analysis_mb = 1000
            self.chunk_size = 50000

    def validate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generic validate method for backward compatibility."""
        logger.info(f"Validating DataFrame with {len(df)} rows for processing")
        return self.validate_for_upload(df)

    def validate_for_upload(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate DataFrame for initial upload."""
        max_bytes = self.max_upload_mb * 1024 * 1024
        memory_usage = df.memory_usage(deep=True).sum()

        if memory_usage > max_bytes:
            raise ValidationError(
                f"DataFrame too large for upload: {memory_usage/1024/1024:.1f}MB > {self.max_upload_mb}MB"
            )

        return self._sanitize_dataframe(df)

    def validate_for_analysis(self, df: pd.DataFrame) -> tuple[pd.DataFrame, bool]:
        """Validate DataFrame for analysis, return (df, needs_chunking)."""
        max_bytes = self.max_analysis_mb * 1024 * 1024
        memory_usage = df.memory_usage(deep=True).sum()

        logger.info(
            f"DataFrame analysis validation: {len(df)} rows, {memory_usage/1024/1024:.1f}MB memory usage"
        )

        # Clean the DataFrame first
        df = self._sanitize_dataframe(df)

        # Only use chunked processing for very large data sets
        needs_chunking = (
            memory_usage > max_bytes
            or len(df) > DataProcessingLimits.CHUNKING_ROW_THRESHOLD
        )

        if needs_chunking:
            logger.info(
                f"Large DataFrame detected: {len(df)} rows, {memory_usage/1024/1024:.1f}MB. Chunked processing enabled."
            )
        else:
            logger.info(
                f"Regular processing for {len(df)} rows - FULL DATASET ANALYSIS"
            )

        return df, needs_chunking

    def get_optimal_chunk_size(self, df: pd.DataFrame) -> int:
        """Calculate an optimal chunk size for processing."""
        memory_usage = df.memory_usage(deep=True).sum()
        max_bytes = self.max_analysis_mb * 1024 * 1024

        total_rows = len(df)
        logger.info(
            f"🔢 Calculating chunk size for {total_rows:,} rows ({memory_usage/1024/1024:.1f}MB)"
        )

        # For small datasets process everything at once
        if (
            memory_usage <= max_bytes
            and total_rows <= DataProcessingLimits.SMALL_DATASET_ROW_THRESHOLD
        ):
            logger.info(f"✅ Small dataset: processing all {total_rows:,} rows at once")
            return total_rows

        # Calculate a chunk size based on memory usage
        calculated_chunk_size = int((total_rows * max_bytes) / memory_usage)

        # Clamp chunk size to allowed limits
        optimal_chunk_size = max(
            calculated_chunk_size, DataProcessingLimits.MIN_CHUNK_SIZE
        )
        optimal_chunk_size = min(
            optimal_chunk_size, DataProcessingLimits.MAX_CHUNK_SIZE
        )

        # Use the calculated size rather than the configuration default
        final_chunk_size = optimal_chunk_size

        # Avoid tiny chunks for small datasets
        if total_rows < DataProcessingLimits.SMALL_DATA_CHUNK_ROWS:
            final_chunk_size = total_rows

        logger.info(
            f"📊 Chunk size calculation: {total_rows:,} rows → {final_chunk_size:,} per chunk"
        )
        logger.info(
            f"📈 Will create {(total_rows + final_chunk_size - 1) // final_chunk_size} chunks"
        )

        return final_chunk_size

    def _sanitize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Sanitize DataFrame using shared helpers."""
        # Check for potential CSV injection before sanitization
        for col in df.select_dtypes(include=["object"]).columns:
            if df[col].astype(str).str.startswith(("=", "+", "-", "@")).any():
                logger.warning(f"Potential CSV injection detected in column '{col}'")
                raise ValidationError(f"Formula detected in column '{col}'")

        sanitized = UnicodeProcessor.sanitize_dataframe(df)

        return sanitized
