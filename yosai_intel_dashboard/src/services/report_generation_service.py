from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import pandas as pd

from yosai_intel_dashboard.src.services.analytics.protocols import ReportGeneratorProtocol
from yosai_intel_dashboard.src.services.summary_report_generator import SummaryReportGenerator


class ReportGenerationService(ReportGeneratorProtocol):
    """Generate analytics reports using :class:`SummaryReportGenerator`."""

    def __init__(self, generator: SummaryReportGenerator | None = None) -> None:
        self._generator = generator or SummaryReportGenerator()

    def generate_summary_report(self, data: pd.DataFrame, template: str = "default") -> Dict[str, Any]:
        return self._generator.analyze_patterns(data)

    def generate_detailed_report(self, data: pd.DataFrame, format: str = "html") -> str:
        summary = self.generate_summary_report(data)
        if format == "json":
            return json.dumps(summary)
        return str(summary)

    def generate_trend_analysis(self, data: pd.DataFrame, time_column: str) -> Dict[str, Any]:
        counts = data[time_column].value_counts().sort_index()
        return {"trend": counts.to_dict()}

    def export_report(self, report_data: Dict[str, Any], format: str, filename: str) -> str:
        path = Path(filename)
        if format == "json":
            path.write_text(json.dumps(report_data))
        else:
            path.write_text(str(report_data))
        return str(path)


__all__ = ["ReportGenerationService"]
