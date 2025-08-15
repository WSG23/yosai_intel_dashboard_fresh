from yosai_intel_dashboard.src.services.export_service import ExportService
from yosai_intel_dashboard.src.repository import FileRepository


class StubFileRepo(FileRepository):
    def __init__(self) -> None:
        self.written: dict[str, str] = {}

    def write_text(self, path, data):
        self.written[str(path)] = data

    def read_text(self, path):  # pragma: no cover - unused
        return self.written[str(path)]


def test_export_to_pdf_uses_repository():
    repo = StubFileRepo()
    svc = ExportService(file_repo=repo)
    out = svc.export_to_pdf({"a": 1}, "report")
    assert repo.written[out] == str({"a": 1})
