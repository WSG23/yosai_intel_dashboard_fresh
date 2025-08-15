from __future__ import annotations

import io
import zipfile

import pytest

from yosai_intel_dashboard.src.services.upload.file_validator import FileValidator


def test_path_traversal(tmp_path):
    validator = FileValidator(tmp_path)
    with pytest.raises(ValueError):
        validator.validate("../../../etc/passwd", "text/plain", b"data")


def test_double_extension(tmp_path):
    validator = FileValidator(tmp_path)
    with pytest.raises(ValueError):
        validator.validate("evil.csv.exe", "application/octet-stream", b"data")


def test_null_bytes(tmp_path):
    validator = FileValidator(tmp_path)
    with pytest.raises(ValueError):
        validator.validate("bad.txt", "text/plain", b"abc\x00def")


def test_mime_mismatch(tmp_path):
    validator = FileValidator(tmp_path)
    with pytest.raises(ValueError):
        validator.validate("data.csv", "application/json", b"a,b\n1,2")


def test_oversize_file(tmp_path):
    validator = FileValidator(tmp_path)
    data = b"a" * (FileValidator.MAX_FILE_SIZE + 1)
    with pytest.raises(ValueError):
        validator.validate("big.csv", "text/csv", data)


def test_zip_bomb_detection(tmp_path):
    validator = FileValidator(tmp_path)
    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("a.txt", b"a" * (FileValidator.MAX_FILE_SIZE * 2))
    bomb = payload.getvalue()
    with pytest.raises(ValueError):
        validator.validate("bomb.txt", "text/plain", bomb)
