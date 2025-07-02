import logging
from typing import Any, Dict, List

import pandas as pd

from analytics.chunked_analytics_controller import ChunkedAnalyticsController
from services.data_validation import DataValidationService
from .result_formatting import regular_analysis

logger = logging.getLogger(__name__)


def analyze_with_chunking(
    df: pd.DataFrame, validator: DataValidationService, analysis_types: List[str]
) -> Dict[str, Any]:
    """Analyze a DataFrame using chunked processing."""
    original_rows = len(df)
    logger.info(f"🚀 Starting COMPLETE analysis for {original_rows:,} rows")

    df, needs_chunking = validator.validate_for_analysis(df)

    validated_rows = len(df)
    logger.info(
        f"📋 After validation: {validated_rows:,} rows, chunking needed: {needs_chunking}"
    )

    if not needs_chunking:
        logger.info("✅ Using regular analysis (no chunking needed)")
        return regular_analysis(df, analysis_types)

    chunk_size = validator.get_optimal_chunk_size(df)
    chunked_controller = ChunkedAnalyticsController(chunk_size=chunk_size)

    logger.info(
        f"🔄 Using chunked analysis: {validated_rows:,} rows, {chunk_size:,} per chunk"
    )

    result = chunked_controller.process_large_dataframe(df, analysis_types)

    result["processing_summary"] = {
        "original_input_rows": original_rows,
        "validated_rows": validated_rows,
        "rows_processed": result.get("rows_processed", validated_rows),
        "chunking_used": True,
        "chunk_size": chunk_size,
        "processing_complete": result.get("rows_processed", 0) == validated_rows,
        "data_integrity_check": (
            "PASS" if result.get("rows_processed", 0) == validated_rows else "FAIL"
        ),
    }

    rows_processed = result.get("rows_processed", 0)
    if rows_processed != validated_rows:
        logger.error(
            f"❌ PROCESSING ERROR: Expected {validated_rows:,} rows, got {rows_processed:,}"
        )
    else:
        logger.info(
            f"✅ SUCCESS: Processed ALL {rows_processed:,} rows successfully"
        )

    return result


__all__ = ["analyze_with_chunking"]
