"""DataFrame security validation with chunked processing support."""

import pandas as pd
from config.dynamic_config import dynamic_config
from utils.unicode_processor import sanitize_data_frame
from .validation_exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)


class DataFrameSecurityValidator:
    """Validate DataFrames for safe processing with chunked analysis support."""

    def __init__(self):
        try:
            from config.dynamic_config import dynamic_config
            self.max_upload_mb = getattr(dynamic_config.security, "max_upload_mb", 500)
            self.max_analysis_mb = getattr(dynamic_config.security, "max_analysis_mb", 1000)
            if hasattr(dynamic_config, 'analytics'):
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

        # Be more conservative about chunking - only chunk very large files
        needs_chunking = memory_usage > max_bytes or len(df) > 100000

        if needs_chunking:
            logger.info(
                f"Large DataFrame detected: {len(df)} rows, {memory_usage/1024/1024:.1f}MB. Chunked processing enabled."
            )
        else:
            logger.info(f"Regular processing for {len(df)} rows")

        return df, needs_chunking

    def get_optimal_chunk_size(self, df: pd.DataFrame) -> int:
        """Calculate optimal chunk size based on DataFrame characteristics."""
        memory_usage = df.memory_usage(deep=True).sum()
        max_bytes = self.max_analysis_mb * 1024 * 1024

        if memory_usage <= max_bytes and len(df) <= 100000:
            logger.info(f"Small dataset: processing all {len(df)} rows at once")
            return len(df)

        calculated_chunk_size = int((len(df) * max_bytes) / memory_usage)
        optimal_chunk_size = max(calculated_chunk_size, 25000)
        final_chunk_size = min(optimal_chunk_size, self.chunk_size)

        logger.info(f"Calculated chunk size: {final_chunk_size} for {len(df)} total rows")
        return final_chunk_size

    def _sanitize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Sanitize DataFrame using shared helpers."""
        # Check for potential CSV injection before sanitization
        for col in df.select_dtypes(include=["object"]).columns:
            if df[col].astype(str).str.startswith(("=", "+", "-", "@")).any():
                logger.warning(
                    f"Potential CSV injection detected in column '{col}'"
                )
                raise ValidationError(
                    f"Formula detected in column '{col}'"
                )

        sanitized = sanitize_data_frame(df)

        return sanitized

