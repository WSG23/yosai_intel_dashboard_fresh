from __future__ import annotations

from yosai_intel_dashboard.src.services.upload.protocols import UploadValidatorProtocol
from validation.file_validator import FileValidator


class DummyValidator(UploadValidatorProtocol):
    def validate(self, filename: str, content: str):
        return filename.endswith(".csv"), "bad"

    def to_json(self) -> str:
        return "{}"


def test_file_validator_calls_validator():
    fv = FileValidator(DummyValidator())
    errors = fv.validate_files(["data"], ["test.txt"])
    assert "test.txt" in errors
