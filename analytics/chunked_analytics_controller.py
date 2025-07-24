#!/usr/bin/env python3
"""Chunked analytics processing for large DataFrames.

Ensures that all chunks are processed without data loss.
"""

import logging
from typing import Any, Dict, Iterator, List

import numpy as np
import pandas as pd

from config.constants import DEFAULT_CHUNK_SIZE, AnalysisThresholds, AnalyticsConstants

logger = logging.getLogger(__name__)


class ChunkedAnalyticsController:
    """Handle analytics processing for large DataFrames using chunking."""

    def __init__(self, chunk_size: int = None, max_workers: int = None) -> None:
        try:
            from config.dynamic_config import dynamic_config

            if hasattr(dynamic_config, "analytics"):
                self.chunk_size = chunk_size or getattr(
                    dynamic_config.analytics, "chunk_size", DEFAULT_CHUNK_SIZE
                )
                self.max_workers = max_workers or getattr(
                    dynamic_config.analytics, "max_workers", 4
                )
            else:
                self.chunk_size = chunk_size or DEFAULT_CHUNK_SIZE
                self.max_workers = max_workers or 4
        except Exception:
            self.chunk_size = chunk_size or DEFAULT_CHUNK_SIZE
            self.max_workers = max_workers or 4

        # Ensure chunk size is at least the configured minimum
        self.chunk_size = max(self.chunk_size, AnalyticsConstants.min_chunk_size)
        logger.info(
            f"ChunkedAnalyticsController initialized: chunk_size={self.chunk_size}"
        )

    def _create_empty_results(self) -> Dict[str, Any]:
        """Return a fresh results dictionary with set fields."""
        return {
            "total_events": 0,
            "unique_users": set(),
            "unique_doors": set(),
            "successful_events": 0,
            "failed_events": 0,
            "security_issues": [],
            "anomalies": [],
            "behavioral_patterns": {},
            "temporal_patterns": {},
        }

    def process_large_dataframe(
        self, df: pd.DataFrame, analysis_types: List[str]
    ) -> Dict[str, Any]:
        """Process a large DataFrame using chunked analysis."""
        total_rows = len(df)
        logger.info(f"🔄 Starting COMPLETE chunked analysis for {total_rows:,} rows")
        logger.info(f"📊 Chunk size: {self.chunk_size:,}")

        # Initialize aggregated results using helper for consistency
        aggregated_results = self._create_empty_results()
        aggregated_results.update(
            {
                "date_range": {"start": None, "end": None},
                "rows_processed": 0,
            }
        )

        chunks_processed = 0
        total_chunks = (len(df) + self.chunk_size - 1) // self.chunk_size

        logger.info(
            f"🎯 Will process {total_chunks} chunks to analyze ALL {total_rows:,} rows"
        )

        # Process all chunks with detailed logging
        for chunk_df in self._chunk_dataframe(df):
            chunk_size_actual = len(chunk_df)
            logger.info(
                f"📦 Processing chunk {chunks_processed + 1}/{total_chunks}: {chunk_size_actual:,} rows"
            )

            # Process this chunk
            chunk_results = self._process_chunk(chunk_df, analysis_types)

            # Aggregate results from this chunk
            self._aggregate_results(aggregated_results, chunk_results)

            chunks_processed += 1
            aggregated_results["rows_processed"] += chunk_size_actual

            # Progress logging every chunk for debugging
            logger.info(
                f"✅ Completed chunk {chunks_processed}/{total_chunks} "
                f"({aggregated_results['rows_processed']:,}/{total_rows:,} rows processed)"
            )

        # Verify all chunks were processed
        if aggregated_results["rows_processed"] != total_rows:
            logger.error(
                f"❌ CHUNK PROCESSING ERROR: Only processed {aggregated_results['rows_processed']:,} of {total_rows:,} rows!"
            )
        else:
            logger.info(
                f"🎉 SUCCESS: Processed ALL {aggregated_results['rows_processed']:,} rows in {chunks_processed} chunks"
            )

        return self._finalize_results(aggregated_results)

    def _chunk_dataframe(self, df: pd.DataFrame) -> Iterator[pd.DataFrame]:
        """Generate DataFrame chunks ensuring no data loss."""
        total_rows = len(df)
        chunks_yielded = 0
        rows_yielded = 0

        logger.info(
            f"🔢 Chunking {total_rows:,} rows with chunk size {self.chunk_size:,}"
        )

        for i in range(0, total_rows, self.chunk_size):
            end_idx = min(i + self.chunk_size, total_rows)
            chunk = df.iloc[i:end_idx].copy()

            chunks_yielded += 1
            rows_yielded += len(chunk)

            logger.debug(
                f"📦 Yielding chunk {chunks_yielded}: rows {i:,} to {end_idx-1:,} ({len(chunk):,} rows)"
            )
            yield chunk

        logger.info(
            f"✅ Chunking complete: {chunks_yielded} chunks, {rows_yielded:,} total rows"
        )

    def _validate_timestamp_column(
        self, df: pd.DataFrame, column: str = "timestamp"
    ) -> pd.DataFrame:
        """Validate and clean timestamp column in DataFrame.

        Converts the column to ``datetime`` and removes any rows with malformed or
        out-of-range timestamps. A warning is logged when invalid values are
        encountered.
        """

        if column not in df.columns:
            return df

        # Operate on a shallow copy to avoid mutating the caller's DataFrame

        df = df.copy(deep=False)
        df[column] = pd.to_datetime(df[column], errors="coerce")

        invalid_mask = df[column].isna()
        if invalid_mask.any():
            logger.warning(
                f"{invalid_mask.sum()} malformed timestamps removed from column '{column}'"
            )
            df = df[~invalid_mask]

        try:
            df = df[
                (df[column] >= pd.Timestamp("1970-01-01"))
                & (df[column] <= pd.Timestamp("2100-12-31"))
            ]
        except Exception as e:  # pragma: no cover - best effort
            logger.debug(f"Timestamp range filter failed: {e}")

        return df

    def _process_chunk(
        self, chunk_df: pd.DataFrame, analysis_types: List[str]
    ) -> Dict[str, Any]:
        """Process a single chunk for all analysis types."""
        logger.debug(f"🔍 Processing chunk with {len(chunk_df):,} rows")

        results = self._create_empty_results()
        results["total_events"] = len(chunk_df)

        # Detect likely column names flexibly
        user_col = None
        door_col = None
        result_col = None
        for col in chunk_df.columns:
            norm = col.lower().replace(" ", "_")
            if user_col is None and any(k in norm for k in ["person", "user"]):
                user_col = col
            if door_col is None and any(k in norm for k in ["door", "device"]):
                door_col = col
            if result_col is None and any(k in norm for k in ["result", "status"]):
                result_col = col

        if user_col:
            unique_users = chunk_df[user_col].dropna().unique()
            results["unique_users"] = set(str(u) for u in unique_users)
            logger.debug(f"Found {len(results['unique_users'])} unique users in chunk")

        if door_col:
            unique_doors = chunk_df[door_col].dropna().unique()
            results["unique_doors"] = set(str(d) for d in unique_doors)
            logger.debug(f"Found {len(results['unique_doors'])} unique doors in chunk")

        if result_col:
            result_series = chunk_df[result_col].astype(str).str.lower()
            success_patterns = ["grant", "allow", "success", "permit", "approved"]
            failure_patterns = ["deny", "fail", "block", "reject", "denied", "failed"]
            success_mask = result_series.str.contains(
                "|".join(success_patterns), na=False
            )
            failure_mask = result_series.str.contains(
                "|".join(failure_patterns), na=False
            )
            results["successful_events"] = int(success_mask.sum())
            if failure_mask.any():
                results["failed_events"] = int(failure_mask.sum())
            else:
                results["failed_events"] = len(chunk_df) - results["successful_events"]
            logger.debug(
                f"Chunk access results: {results['successful_events']} success, {results['failed_events']} failed"
            )

        # Process analysis types
        if "security" in analysis_types:
            results["security_issues"].extend(self._analyze_security_chunk(chunk_df))

        if "anomaly" in analysis_types:
            results["anomalies"].extend(self._analyze_anomalies_chunk(chunk_df))

        if "behavior" in analysis_types:
            results["behavioral_patterns"] = self._analyze_behavior_chunk(chunk_df)

        if "trends" in analysis_types:
            results["temporal_patterns"] = self._analyze_trends_chunk(chunk_df)

        logger.debug(
            f"✅ Chunk processing complete: {results['total_events']} events processed"
        )
        return results

    def _analyze_security_chunk(self, chunk_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Analyze security patterns in chunk."""
        issues: List[Dict[str, Any]] = []

        if "access_result" in chunk_df.columns and "person_id" in chunk_df.columns:
            # Identify users with repeated failures
            failure_patterns = ["deny", "fail", "block", "reject", "denied", "failed"]
            failed_attempts = chunk_df[
                chunk_df["access_result"]
                .str.lower()
                .str.contains("|".join(failure_patterns), case=False, na=False)
            ]

            if len(failed_attempts) > 0:
                user_failures = failed_attempts.groupby("person_id").size()
                high_failure_users = user_failures[
                    user_failures >= AnalysisThresholds.failed_attempt_threshold
                ]

                for user_id, failure_count in high_failure_users.items():
                    issues.append(
                        {
                            "type": "high_failure_rate",
                            "user_id": str(user_id),
                            "failure_count": int(failure_count),
                            "severity": (
                                "high"
                                if failure_count
                                >= AnalysisThresholds.high_failure_severity
                                else "medium"
                            ),
                        }
                    )

        return issues

    def _analyze_anomalies_chunk(self, chunk_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Analyze anomalies in chunk."""
        anomalies: List[Dict[str, Any]] = []

        if "timestamp" in chunk_df.columns and "person_id" in chunk_df.columns:
            try:
                chunk_df = self._validate_timestamp_column(chunk_df)
                if chunk_df.empty:
                    logger.warning("Chunk has no valid timestamps for anomaly analysis")
                    return anomalies

                chunk_df = chunk_df.sort_values(["person_id", "timestamp"])

                for user_id in chunk_df["person_id"].unique():
                    user_data = chunk_df[chunk_df["person_id"] == user_id]
                    if len(user_data) > 1:
                        time_diffs = user_data["timestamp"].diff().dt.total_seconds()
                        rapid_attempts = (
                            time_diffs < AnalysisThresholds.rapid_attempt_seconds
                        ).sum()

                        if rapid_attempts > AnalysisThresholds.rapid_attempt_threshold:
                            anomalies.append(
                                {
                                    "type": "rapid_attempts",
                                    "user_id": str(user_id),
                                    "rapid_count": int(rapid_attempts),
                                    "severity": "high",
                                }
                            )
            except Exception as e:
                logger.warning(f"Anomaly analysis failed for chunk: {e}")

        return anomalies

    def _analyze_behavior_chunk(self, chunk_df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze behavioral patterns in chunk."""
        patterns: Dict[str, Any] = {}

        if "person_id" in chunk_df.columns:
            user_activity = chunk_df.groupby("person_id").size()
            patterns["avg_activity"] = (
                float(user_activity.mean()) if len(user_activity) > 0 else 0.0
            )
            patterns["max_activity"] = (
                int(user_activity.max()) if len(user_activity) > 0 else 0
            )
            patterns["active_users"] = len(user_activity)

        return patterns

    def _analyze_trends_chunk(self, chunk_df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze temporal trends in chunk."""
        patterns: Dict[str, Any] = {}

        if "timestamp" in chunk_df.columns:
            try:
                chunk_df = self._validate_timestamp_column(chunk_df)

                if len(chunk_df) > 0:
                    patterns["date_range"] = {
                        "start": chunk_df["timestamp"].min(),
                        "end": chunk_df["timestamp"].max(),
                    }

                    chunk_df["hour"] = chunk_df["timestamp"].dt.hour
                    patterns["hourly_distribution"] = (
                        chunk_df["hour"].value_counts().to_dict()
                    )
            except Exception as e:
                logger.warning(f"Trends analysis failed for chunk: {e}")

        return patterns

    def _aggregate_results(
        self, aggregated: Dict[str, Any], chunk_results: Dict[str, Any]
    ) -> None:
        """Aggregate chunk results into overall results."""
        # Basic counts
        aggregated["total_events"] += chunk_results["total_events"]
        aggregated["successful_events"] += chunk_results["successful_events"]
        aggregated["failed_events"] += chunk_results["failed_events"]

        # Combine user and door sets
        aggregated["unique_users"].update(chunk_results["unique_users"])
        aggregated["unique_doors"].update(chunk_results["unique_doors"])

        # Lists
        aggregated["security_issues"].extend(chunk_results["security_issues"])
        aggregated["anomalies"].extend(chunk_results["anomalies"])

        # Aggregate behavioral pattern metrics
        if chunk_results["behavioral_patterns"]:
            for key, value in chunk_results["behavioral_patterns"].items():
                if key not in aggregated["behavioral_patterns"]:
                    aggregated["behavioral_patterns"][key] = []
                if isinstance(value, (int, float)):
                    aggregated["behavioral_patterns"][key].append(value)

        # Merge chunk date ranges
        if chunk_results["temporal_patterns"].get("date_range"):
            chunk_range = chunk_results["temporal_patterns"]["date_range"]
            if aggregated["date_range"]["start"] is None:
                aggregated["date_range"] = chunk_range.copy()
            else:
                if chunk_range["start"] < aggregated["date_range"]["start"]:
                    aggregated["date_range"]["start"] = chunk_range["start"]
                if chunk_range["end"] > aggregated["date_range"]["end"]:
                    aggregated["date_range"]["end"] = chunk_range["end"]

    def _finalize_results(self, aggregated: Dict[str, Any]) -> Dict[str, Any]:
        """Finalize and clean up aggregated results."""
        # Convert sets to counts
        aggregated["unique_users"] = len(aggregated["unique_users"])
        aggregated["unique_doors"] = len(aggregated["unique_doors"])

        # Calculate success rate
        if aggregated["total_events"] > 0:
            aggregated["success_rate"] = (
                aggregated["successful_events"] / aggregated["total_events"]
            )
        else:
            aggregated["success_rate"] = 0.0

        # Average behavioral pattern values
        if aggregated["behavioral_patterns"]:
            for key, values in aggregated["behavioral_patterns"].items():
                if isinstance(values, list) and len(values) > 0:
                    aggregated["behavioral_patterns"][key] = float(np.mean(values))

        # Convert date range values to ISO strings
        if aggregated["date_range"]["start"]:
            aggregated["date_range"]["start"] = aggregated["date_range"][
                "start"
            ].isoformat()
        if aggregated["date_range"]["end"]:
            aggregated["date_range"]["end"] = aggregated["date_range"][
                "end"
            ].isoformat()

        logger.info(
            f"🎉 FINAL RESULTS: {aggregated['total_events']:,} total events, "
            f"{aggregated['unique_users']:,} users, {aggregated['unique_doors']:,} doors"
        )

        return aggregated
