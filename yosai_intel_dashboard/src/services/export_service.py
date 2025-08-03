"""Stub export service implementing ExportServiceProtocol."""

from __future__ import annotations

from typing import Any, Dict

from ..repository import FileRepository, LocalFileRepository


class ExportService:
    def __init__(self, file_repo: FileRepository | None = None) -> None:
        self._file_repo = file_repo or LocalFileRepository()

    def export_to_parquet(self, data, filename: str) -> str:
        data.to_parquet(filename, index=False)
        return filename

    def export_to_pdf(self, data: Dict[str, Any], template: str) -> str:
        path = f"{template}.pdf"
        self._file_repo.write_text(path, str(data))
        return path

    def get_export_status(self, export_id: str) -> Dict[str, Any]:
        return {"export_id": export_id, "status": "complete"}
