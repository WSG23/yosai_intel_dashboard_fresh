"""Simple report generator stub."""

from __future__ import annotations

from typing import Any, Dict

import pandas as pd

from .protocols import ReportGeneratorProtocol


class ReportGenerator(ReportGeneratorProtocol):
    def generate_summary_report(self, data: pd.DataFrame) -> Dict[str, Any]:
        return {"records": len(data)}

    def generate_detailed_report(self, data: pd.DataFrame, template: str) -> str:
        return f"Report based on {len(data)} records using {template}"
