"""Chunked analytics processing for large DataFrames."""

import pandas as pd
import logging
from typing import Dict, Any, List, Iterator
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np

logger = logging.getLogger(__name__)


class ChunkedAnalyticsController:
    """Handle analytics processing for large DataFrames using chunking."""

    def __init__(self, chunk_size: int = None, max_workers: int = None) -> None:
        try:
            from config.dynamic_config import dynamic_config
            if hasattr(dynamic_config, 'analytics'):
                self.chunk_size = chunk_size or getattr(dynamic_config.analytics, 'chunk_size', 10000)
                self.max_workers = max_workers or getattr(dynamic_config.analytics, 'max_workers', 4)
            else:
                self.chunk_size = chunk_size or 10000
                self.max_workers = max_workers or 4
        except Exception:
            self.chunk_size = chunk_size or 10000
            self.max_workers = max_workers or 4

    def process_large_dataframe(self, df: pd.DataFrame, analysis_types: List[str]) -> Dict[str, Any]:
        """Process large DataFrame using chunked analysis."""
        total_rows = len(df)
        logger.info(
            f"Starting chunked analysis for {total_rows:,} rows with chunk size {self.chunk_size:,}"
        )

        aggregated_results = {
            "total_events": 0,
            "unique_users": set(),
            "unique_doors": set(),
            "successful_events": 0,
            "failed_events": 0,
            "security_issues": [],
            "anomalies": [],
            "behavioral_patterns": {},
            "temporal_patterns": {},
            "date_range": {"start": None, "end": None},
            "rows_processed": 0,
        }

        chunks_processed = 0
        total_chunks = (len(df) + self.chunk_size - 1) // self.chunk_size

        logger.info(f"Processing {total_chunks} chunks of size {self.chunk_size}")

        for chunk_df in self._chunk_dataframe(df):
            chunk_results = self._process_chunk(chunk_df, analysis_types)
            self._aggregate_chunk_results(aggregated_results, chunk_results)

            chunks_processed += 1
            aggregated_results["rows_processed"] += len(chunk_df)

            if chunks_processed % 5 == 0:
                logger.info(
                    f"Processed {chunks_processed}/{total_chunks} chunks ({aggregated_results['rows_processed']:,}/{total_rows:,} rows)"
                )

        logger.info(
            f"Chunked analysis complete: {aggregated_results['rows_processed']:,} total rows processed"
        )
        return self._finalize_results(aggregated_results)

    def _chunk_dataframe(self, df: pd.DataFrame) -> Iterator[pd.DataFrame]:
        """Generate DataFrame chunks."""
        for i in range(0, len(df), self.chunk_size):
            yield df.iloc[i : i + self.chunk_size].copy()

    def _process_chunk(self, chunk_df: pd.DataFrame, analysis_types: List[str]) -> Dict[str, Any]:
        """Process a single chunk for all analysis types."""
        results = {
            "total_events": len(chunk_df),
            "unique_users": set(),
            "unique_doors": set(),
            "successful_events": 0,
            "failed_events": 0,
            "security_issues": [],
            "anomalies": [],
            "behavioral_patterns": {},
            "temporal_patterns": {},
        }

        if "person_id" in chunk_df.columns:
            results["unique_users"] = set(chunk_df["person_id"].dropna().unique())

        if "door_id" in chunk_df.columns:
            results["unique_doors"] = set(chunk_df["door_id"].dropna().unique())

        if "access_result" in chunk_df.columns:
            success_mask = chunk_df["access_result"].str.contains(
                "Grant|Allow|Success", case=False, na=False
            )
            results["successful_events"] = success_mask.sum()
            results["failed_events"] = len(chunk_df) - results["successful_events"]

        if "security" in analysis_types:
            results["security_issues"].extend(self._analyze_security_chunk(chunk_df))

        if "anomaly" in analysis_types:
            results["anomalies"].extend(self._analyze_anomalies_chunk(chunk_df))

        if "behavior" in analysis_types:
            results["behavioral_patterns"] = self._analyze_behavior_chunk(chunk_df)

        if "trends" in analysis_types:
            results["temporal_patterns"] = self._analyze_trends_chunk(chunk_df)

        return results

    def _analyze_security_chunk(self, chunk_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Analyze security patterns in chunk."""
        issues: List[Dict[str, Any]] = []

        if "access_result" in chunk_df.columns:
            failed_attempts = chunk_df[chunk_df["access_result"].str.contains(
                "Deny|Fail|Block", case=False, na=False
            )]

            if len(failed_attempts) > 0:
                user_failures = failed_attempts.groupby("person_id").size()
                high_failure_users = user_failures[user_failures >= 3]

                for user_id, failure_count in high_failure_users.items():
                    issues.append(
                        {
                            "type": "high_failure_rate",
                            "user_id": user_id,
                            "failure_count": failure_count,
                            "severity": "high" if failure_count >= 5 else "medium",
                        }
                    )

        return issues

    def _analyze_anomalies_chunk(self, chunk_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Analyze anomalies in chunk."""
        anomalies: List[Dict[str, Any]] = []

        if "timestamp" in chunk_df.columns and "person_id" in chunk_df.columns:
            chunk_df["timestamp"] = pd.to_datetime(chunk_df["timestamp"], errors="coerce")
            chunk_df = chunk_df.sort_values(["person_id", "timestamp"])

            for user_id in chunk_df["person_id"].unique():
                user_data = chunk_df[chunk_df["person_id"] == user_id]
                if len(user_data) > 1:
                    time_diffs = user_data["timestamp"].diff().dt.total_seconds()
                    rapid_attempts = (time_diffs < 30).sum()

                    if rapid_attempts > 2:
                        anomalies.append(
                            {
                                "type": "rapid_attempts",
                                "user_id": user_id,
                                "rapid_count": rapid_attempts,
                                "severity": "high",
                            }
                        )

        return anomalies

    def _analyze_behavior_chunk(self, chunk_df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze behavioral patterns in chunk."""
        patterns: Dict[str, Any] = {}

        if "person_id" in chunk_df.columns:
            user_activity = chunk_df.groupby("person_id").size()
            patterns["avg_activity"] = user_activity.mean()
            patterns["max_activity"] = user_activity.max()
            patterns["active_users"] = len(user_activity)

        return patterns

    def _analyze_trends_chunk(self, chunk_df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze temporal trends in chunk."""
        patterns: Dict[str, Any] = {}

        if "timestamp" in chunk_df.columns:
            chunk_df["timestamp"] = pd.to_datetime(chunk_df["timestamp"], errors="coerce")
            chunk_df = chunk_df.dropna(subset=["timestamp"])

            if len(chunk_df) > 0:
                patterns["date_range"] = {
                    "start": chunk_df["timestamp"].min(),
                    "end": chunk_df["timestamp"].max(),
                }

                chunk_df["hour"] = chunk_df["timestamp"].dt.hour
                patterns["hourly_distribution"] = chunk_df["hour"].value_counts().to_dict()

        return patterns

    def _aggregate_chunk_results(self, aggregated: Dict[str, Any], chunk_results: Dict[str, Any]) -> None:
        """Aggregate chunk results into overall results."""
        aggregated["total_events"] += chunk_results["total_events"]
        aggregated["successful_events"] += chunk_results["successful_events"]
        aggregated["failed_events"] += chunk_results["failed_events"]

        aggregated["unique_users"].update(chunk_results["unique_users"])
        aggregated["unique_doors"].update(chunk_results["unique_doors"])

        aggregated["security_issues"].extend(chunk_results["security_issues"])
        aggregated["anomalies"].extend(chunk_results["anomalies"])

        if chunk_results["behavioral_patterns"]:
            for key, value in chunk_results["behavioral_patterns"].items():
                if key not in aggregated["behavioral_patterns"]:
                    aggregated["behavioral_patterns"][key] = []
                aggregated["behavioral_patterns"][key].append(value)

        if chunk_results["temporal_patterns"].get("date_range"):
            chunk_range = chunk_results["temporal_patterns"]["date_range"]
            if aggregated["date_range"]["start"] is None:
                aggregated["date_range"] = chunk_range
            else:
                aggregated["date_range"]["start"] = min(
                    aggregated["date_range"]["start"], chunk_range["start"]
                )
                aggregated["date_range"]["end"] = max(
                    aggregated["date_range"]["end"], chunk_range["end"]
                )

    def _finalize_results(self, aggregated: Dict[str, Any]) -> Dict[str, Any]:
        """Finalize and clean up aggregated results."""
        aggregated["unique_users"] = len(aggregated["unique_users"])
        aggregated["unique_doors"] = len(aggregated["unique_doors"])

        if aggregated["total_events"] > 0:
            aggregated["success_rate"] = aggregated["successful_events"] / aggregated["total_events"]
        else:
            aggregated["success_rate"] = 0.0

        if aggregated["behavioral_patterns"]:
            for key, values in aggregated["behavioral_patterns"].items():
                if isinstance(values, list) and len(values) > 0:
                    aggregated["behavioral_patterns"][key] = np.mean(values)

        if aggregated["date_range"]["start"]:
            aggregated["date_range"]["start"] = aggregated["date_range"]["start"].isoformat()
        if aggregated["date_range"]["end"]:
            aggregated["date_range"]["end"] = aggregated["date_range"]["end"].isoformat()

        logger.info(
            f"Chunked analysis complete: {aggregated['total_events']} total events processed"
        )
        return aggregated

