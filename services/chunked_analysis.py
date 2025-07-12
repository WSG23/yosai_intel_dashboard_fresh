import hashlib
import logging
import os
import pickle
from pathlib import Path
from typing import Any, Dict, List

import dask
import pandas as pd
from dask.distributed import Client, LocalCluster

from analytics.chunked_analytics_controller import ChunkedAnalyticsController
from config.config import get_analytics_config
from core.security_validator import SecurityValidator

from .result_formatting import regular_analysis

logger = logging.getLogger(__name__)


def analyze_with_chunking(
    df: pd.DataFrame, validator: SecurityValidator, analysis_types: List[str]
) -> Dict[str, Any]:
    """Analyze a DataFrame using chunked processing."""
    original_rows = len(df)
    logger.info(f"🚀 Starting COMPLETE analysis for {original_rows:,} rows")

    csv_bytes = df.to_csv(index=False).encode("utf-8")
    validator.validate_file_upload("data.csv", csv_bytes)
    needs_chunking = True

    validated_rows = len(df)
    logger.info(
        f"📋 After validation: {validated_rows:,} rows, chunking needed: {needs_chunking}"
    )

    if not needs_chunking:
        logger.info("✅ Using regular analysis (no chunking needed)")
        return regular_analysis(df, analysis_types)

    cfg = get_analytics_config()
    chunk_size = cfg.chunk_size or len(df)
    max_workers = cfg.max_workers or 1
    chunked_controller = ChunkedAnalyticsController(
        chunk_size=chunk_size, max_workers=max_workers
    )

    logger.info(
        f"🔄 Using chunked analysis: {validated_rows:,} rows, {chunk_size:,} per chunk"
    )

    cache_dir = Path(os.getenv("CHUNK_CACHE_DIR", "./chunk_cache"))
    cache_dir.mkdir(parents=True, exist_ok=True)

    def _chunk_key(chunk_df: pd.DataFrame) -> str:
        digest = hashlib.sha256(
            pd.util.hash_pandas_object(chunk_df, index=True).values.tobytes()
        ).hexdigest()
        return digest

    def _process(chunk_df: pd.DataFrame) -> Dict[str, Any]:
        key = _chunk_key(chunk_df)
        cache_file = cache_dir / f"{key}.pkl"
        if cache_file.exists():
            with open(cache_file, "rb") as fh:
                return pickle.load(fh)
        result = chunked_controller._process_chunk(chunk_df, analysis_types)
        with open(cache_file, "wb") as fh:
            pickle.dump(result, fh)
        return result

    cluster = LocalCluster(n_workers=max_workers, threads_per_worker=1)
    client = Client(cluster)

    chunks = list(chunked_controller._chunk_dataframe(df))
    tasks = [dask.delayed(_process)(chunk) for chunk in chunks]
    chunk_results = dask.compute(*tasks)

    client.close()
    cluster.close()

    aggregated = chunked_controller._create_empty_results()
    aggregated.update({"date_range": {"start": None, "end": None}, "rows_processed": 0})

    for chunk_df, res in zip(chunks, chunk_results):
        chunked_controller._aggregate_results(aggregated, res)
        aggregated["rows_processed"] += len(chunk_df)

    result = chunked_controller._finalize_results(aggregated)

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
        logger.info(f"✅ SUCCESS: Processed ALL {rows_processed:,} rows successfully")

    return result


__all__ = ["analyze_with_chunking"]
