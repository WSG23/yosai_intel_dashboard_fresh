from __future__ import annotations

import logging
from typing import Any, Dict, List, Tuple

import pandas as pd

from analytics.core.utils import hll_count


logger = logging.getLogger(__name__)


class AnalyticsProcessor:
    """Calculate statistics for analytics results."""

    def calculate_pattern_stats(self, df: pd.DataFrame) -> Tuple[int, int, int, int]:
        total_records = len(df)
        unique_users = hll_count(df["person_id"]) if "person_id" in df.columns else 0
        unique_devices = hll_count(df["door_id"]) if "door_id" in df.columns else 0

        date_span = 0
        if "timestamp" in df.columns:
            ts = pd.to_datetime(df["timestamp"], errors="coerce")
            df["timestamp"] = ts
            if ts.notna().any():
                date_span = (ts.max() - ts.min()).days
        logger.info("\ud83d\udcc8 STATISTICS:")
        logger.info("   Total records: %s", f"{total_records:,}")
        logger.info("   Unique users: %s", f"{unique_users:,}")
        logger.info("   Unique devices: %s", f"{unique_devices:,}")
        if date_span:
            logger.info("   Date span: %s days", date_span)
        return total_records, unique_users, unique_devices, date_span

    def analyze_user_patterns(
        self, df: pd.DataFrame, unique_users: int
    ) -> Tuple[List[str], List[str], List[str]]:
        power_users: List[str] = []
        regular_users: List[str] = []
        occasional_users: List[str] = []
        if "person_id" in df.columns and unique_users > 0:
            user_stats = df["person_id"].value_counts()
            if not user_stats.empty:
                q20, q80 = user_stats.quantile([0.2, 0.8])
                power_users = user_stats[user_stats.gt(q80)].index.tolist()
                regular_users = user_stats[user_stats.between(q20, q80)].index.tolist()
                occasional_users = user_stats[user_stats.lt(q20)].index.tolist()
        logger.info("   Power users: %s", len(power_users))
        logger.info("   Regular users: %s", len(regular_users))
        logger.info("   Occasional users: %s", len(occasional_users))
        return power_users, regular_users, occasional_users

    def analyze_device_patterns(
        self, df: pd.DataFrame, unique_devices: int
    ) -> Tuple[List[str], List[str], List[str]]:
        high_traffic: List[str] = []
        moderate_traffic: List[str] = []
        low_traffic: List[str] = []
        if "door_id" in df.columns and unique_devices > 0:
            device_stats = df["door_id"].value_counts()
            if not device_stats.empty:
                q20, q80 = device_stats.quantile([0.2, 0.8])
                high_traffic = device_stats[device_stats.gt(q80)].index.tolist()
                moderate_traffic = device_stats[
                    device_stats.between(q20, q80)
                ].index.tolist()
                low_traffic = device_stats[device_stats.lt(q20)].index.tolist()
        logger.info("   High traffic devices: %s", len(high_traffic))
        logger.info("   Moderate traffic devices: %s", len(moderate_traffic))
        logger.info("   Low traffic devices: %s", len(low_traffic))
        return high_traffic, moderate_traffic, low_traffic

    def count_interactions(self, df: pd.DataFrame) -> int:
        if "person_id" in df.columns and "door_id" in df.columns:
            interaction_pairs = df.groupby(["person_id", "door_id"]).size()
            return len(interaction_pairs)
        return 0

    def calculate_success_rate(self, df: pd.DataFrame) -> float:
        if "access_result" in df.columns:
            success_mask = df["access_result"].str.contains(
                "grant|allow|success|permit", case=False, na=False
            )
            return float(success_mask.mean())
        return 0.0


__all__ = ["AnalyticsProcessor"]
