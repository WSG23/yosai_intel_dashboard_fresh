"""Stub export service implementing ExportServiceProtocol."""

from __future__ import annotations

from typing import Any, Dict

import pandas as pd

from yosai_intel_dashboard.src.core.protocols import ExportServiceProtocol


class ExportService(ExportServiceProtocol):
    def export_to_parquet(self, data: pd.DataFrame, filename: str) -> str:
        data.to_parquet(filename, index=False)
        return filename

    def export_to_pdf(self, data: Dict[str, Any], template: str) -> str:
        path = f"{template}.pdf"
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(str(data))
        return path

    def get_export_status(self, export_id: str) -> Dict[str, Any]:
        return {"export_id": export_id, "status": "complete"}
