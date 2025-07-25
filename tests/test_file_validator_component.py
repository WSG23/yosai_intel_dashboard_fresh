from services.upload.core.file_validator import FileValidator
from services.upload.protocols import UploadValidatorProtocol

class DummyValidator(UploadValidatorProtocol):
    def validate(self, filename: str, content: str):
        return filename.endswith(".csv"), "bad"

    def to_json(self) -> str:
        return "{}"


def test_file_validator_calls_validator():
    fv = FileValidator(DummyValidator())
    errors = fv.validate_files(["data"], ["test.txt"])
    assert "test.txt" in errors
