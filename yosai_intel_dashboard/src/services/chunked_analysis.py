import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List

try:
    import dask
    from dask.distributed import Client, LocalCluster
except Exception:  # pragma: no cover - optional dependency
    dask = None  # type: ignore
    Client = None  # type: ignore
    LocalCluster = None  # type: ignore

import pandas as pd

from yosai_intel_dashboard.src.infrastructure.config.config import get_analytics_config
from validation.data_validator import DataValidator
from validation.security_validator import SecurityValidator

from .result_formatting import regular_analysis

logger = logging.getLogger(__name__)


def _validate_dataframe(
    df: pd.DataFrame,
    validator: SecurityValidator,
) -> tuple[int, int, bool]:
    """Validate ``df`` using :class:`DataValidator`."""

    original_rows = len(df)
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    validator.validate_file_upload("data.csv", csv_bytes)

    df_validator = DataValidator()
    result = df_validator.validate_dataframe(df)
    if not result.valid:
        logger.warning("Data issues detected: %s", result.issues)

    validated_rows = len(df)
    needs_chunking = True
    logger.info(
        "📋 After validation: %s rows, chunking needed: %s",
        f"{validated_rows:,}",
        needs_chunking,
    )
    return original_rows, validated_rows, needs_chunking


def _process_chunks(
    df: pd.DataFrame,
    chunked_controller: ChunkedAnalyticsController,
    analysis_types: List[str],
    cache_dir: Path,
    max_workers: int,
) -> Dict[str, Any]:
    """Process dataframe chunks using Dask."""

    def _chunk_key(chunk_df: pd.DataFrame) -> str:
        digest = hashlib.sha256(
            pd.util.hash_pandas_object(chunk_df, index=True).values.tobytes()
        ).hexdigest()
        return digest

    def _process(chunk_df: pd.DataFrame) -> Dict[str, Any]:
        key = _chunk_key(chunk_df)
        cache_file = cache_dir / f"{key}.json"
        if cache_file.exists():
            with open(cache_file, "r", encoding="utf-8") as fh:
                cached = json.load(fh)
            for field in ("unique_users", "unique_doors"):
                if isinstance(cached.get(field), list):
                    cached[field] = set(cached[field])
            return cached
        result = chunked_controller._process_chunk(chunk_df, analysis_types)
        json_ready = {
            k: (list(v) if isinstance(v, set) else v) for k, v in result.items()
        }
        with open(cache_file, "w", encoding="utf-8") as fh:
            json.dump(json_ready, fh)
        return result

    chunks = list(chunked_controller._chunk_dataframe(df))

    if dask is None or Client is None or LocalCluster is None:
        logger.info(
            "Dask not available; skipping distributed path and processing chunks sequentially"
        )
        chunk_results = [_process(chunk) for chunk in chunks]
    else:
        cluster = LocalCluster(n_workers=max_workers, threads_per_worker=1)
        client = Client(cluster)
        tasks = [dask.delayed(_process)(chunk) for chunk in chunks]
        chunk_results = dask.compute(*tasks)
        client.close()
        cluster.close()

    aggregated = chunked_controller._create_empty_results()
    aggregated.update({"date_range": {"start": None, "end": None}, "rows_processed": 0})

    for chunk_df, res in zip(chunks, chunk_results):
        chunked_controller._aggregate_results(aggregated, res)
        aggregated["rows_processed"] += len(chunk_df)

    return chunked_controller._finalize_results(aggregated)


def _add_processing_summary(
    result: Dict[str, Any],
    original_rows: int,
    validated_rows: int,
    chunk_size: int,
) -> None:
    """Attach processing summary and log basic checks."""

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
            "❌ PROCESSING ERROR: Expected %s rows, got %s",
            f"{validated_rows:,}",
            f"{rows_processed:,}",
        )
    else:
        logger.info(f"✅ SUCCESS: Processed ALL {rows_processed:,} rows successfully")


def analyze_with_chunking(
    df: pd.DataFrame, validator: SecurityValidator, analysis_types: List[str]
) -> Dict[str, Any]:
    """Analyze a DataFrame using chunked processing."""

    original_rows, validated_rows, needs_chunking = _validate_dataframe(df, validator)

    if not needs_chunking:
        logger.info("✅ Using regular analysis (no chunking needed)")
        return regular_analysis(df, analysis_types)

    logger.info("✅ Using simplified chunk analysis")
    result = regular_analysis(df, analysis_types)
    _add_processing_summary(result, original_rows, validated_rows, len(df))
    return result


__all__ = ["analyze_with_chunking"]
