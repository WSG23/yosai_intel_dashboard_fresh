from __future__ import annotations

from typing import Any, Dict, List, Tuple

import pandas as pd

from yosai_intel_dashboard.src.services.summary_report_generator import SummaryReportGenerator


class Calculator:
    """Perform analytics calculations for uploaded data."""

    def __init__(self, generator: SummaryReportGenerator) -> None:
        self.generator = generator

    def calculate_stats(self, df: pd.DataFrame) -> Tuple[int, int, int, int]:
        return self.generator.calculate_stats(df)

    def analyze_users(
        self, df: pd.DataFrame, unique_users: int
    ) -> Tuple[List[str], List[str], List[str]]:
        return self.generator.analyze_users(df, unique_users)

    def analyze_devices(
        self, df: pd.DataFrame, unique_devices: int
    ) -> Tuple[List[str], List[str], List[str]]:
        return self.generator.analyze_devices(df, unique_devices)

    def log_analysis_summary(self, result_total: int, original_rows: int) -> None:
        self.generator.log_analysis_summary(result_total, original_rows)

    def analyze_patterns(self, df: pd.DataFrame, original_rows: int) -> Dict[str, Any]:
        result = self.generator.analyze_patterns(df)
        result_total = result["data_summary"]["total_records"]
        self.log_analysis_summary(result_total, original_rows)
        return result


def create_calculator(
    generator: SummaryReportGenerator | None = None,
) -> "Calculator":
    """Create a :class:`Calculator` with default dependencies."""
    generator = generator or SummaryReportGenerator()
    return Calculator(generator)


__all__ = ["Calculator", "create_calculator"]
