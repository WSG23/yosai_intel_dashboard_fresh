from __future__ import annotations

import logging
from typing import Any, Dict, List, Tuple

import pandas as pd

from .analytics.processor import AnalyticsProcessor
from .base_database_service import BaseDatabaseService
from .summary_reporter import format_patterns_result

logger = logging.getLogger(__name__)


class SummaryReportGenerator(BaseDatabaseService):
    """Generate summary reports for pattern analysis."""

    @property
    def processor(self) -> AnalyticsProcessor:
        if not hasattr(self, "_processor"):
            self._processor = AnalyticsProcessor()
        return self._processor

    def calculate_stats(self, df: pd.DataFrame) -> Tuple[int, int, int, int]:
        """Return basic statistics for pattern analysis."""
        return self.processor.calculate_pattern_stats(df)

    def analyze_users(
        self, df: pd.DataFrame, unique_users: int
    ) -> Tuple[List[str], List[str], List[str]]:
        """Return user activity groupings."""
        return self.processor.analyze_user_patterns(df, unique_users)

    def analyze_devices(
        self, df: pd.DataFrame, unique_devices: int
    ) -> Tuple[List[str], List[str], List[str]]:
        """Return device activity groupings."""
        return self.processor.analyze_device_patterns(df, unique_devices)

    def count_interactions(self, df: pd.DataFrame) -> int:
        return self.processor.count_interactions(df)

    def calculate_success_rate(self, df: pd.DataFrame) -> float:
        return self.processor.calculate_success_rate(df)

    def log_analysis_summary(self, result_total: int, original_rows: int) -> None:
        """Log summary details after pattern analysis."""
        logger.info("🎉 UNIQUE PATTERNS ANALYSIS COMPLETE")
        logger.info("   Result total_records: %s", f"{result_total:,}")

        if result_total == original_rows:
            logger.info("✅ SUCCESS: Correctly showing %s rows", f"{result_total:,}")
        elif result_total != original_rows:
            logger.warning(
                "⚠️  Unexpected count: %s (expected %s)",
                f"{result_total:,}",
                f"{original_rows:,}",
            )

    def analyze_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Run the unique patterns analysis on ``df``."""
        total_records, unique_users, unique_devices, date_span = self.calculate_stats(
            df
        )

        power_users, regular_users, occasional_users = self.analyze_users(
            df, unique_users
        )
        high_traffic, moderate_traffic, low_traffic = self.analyze_devices(
            df, unique_devices
        )

        total_interactions = self.count_interactions(df)
        success_rate = self.calculate_success_rate(df)

        return format_patterns_result(
            total_records,
            unique_users,
            unique_devices,
            date_span,
            power_users,
            regular_users,
            occasional_users,
            high_traffic,
            moderate_traffic,
            low_traffic,
            total_interactions,
            success_rate,
        )


__all__ = ["SummaryReportGenerator"]
